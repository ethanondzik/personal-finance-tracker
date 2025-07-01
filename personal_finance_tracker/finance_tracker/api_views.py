from rest_framework import viewsets, permissions
from .models import Transaction, Account, Category, Subscription, Budget, CustomNotification
from .serializers import (
    TransactionSerializer, AccountSerializer, CategorySerializer,
    SubscriptionSerializer, BudgetSerializer, CustomNotificationSerializer
)

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.response import Response
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.filters import SearchFilter, OrderingFilter
from datetime import datetime, timedelta
from django.db.models import Sum, Count, Q, Min, Max
from django.utils import timezone
from zoneinfo import ZoneInfo

from .filters import TransactionFilter
from .pagination import TransactionPagination


class IsOwner(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to view or edit it.
    """
    def has_object_permission(self, request, view, obj):
        return obj.user == request.user

class UserScopedViewSet(viewsets.ModelViewSet):
    """
    A base ViewSet that automatically filters querysets by the current user
    and sets the user on creation.
    """
    permission_classes = [permissions.IsAuthenticated, IsOwner]

    def get_queryset(self):
        """
        This view should return a list of all the objects
        for the currently authenticated user.
        """
        return self.queryset.filter(user=self.request.user)

    def perform_create(self, serializer):
        """
        Set the user of the object to the current user.
        """
        serializer.save(user=self.request.user)



# --- ViewSets for each model ---

class TransactionViewSet(UserScopedViewSet):
    queryset = Transaction.objects.all().select_related('account', 'category')
    serializer_class = TransactionSerializer
    filterset_class = TransactionFilter
    pagination_class = TransactionPagination

    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]

    # Search fields for the SearchFilter
    search_fields = ['description', 'category__name', 'account__account_number']
    
    # Ordering fields
    ordering_fields = [
        'date', 'amount', 'transaction_type', 'created_at', 
        'account__account_number', 'category__name', 'method'
    ]
    ordering = ['-date', '-id']  # Default ordering

    def get_queryset(self):
        """Enhanced queryset with optimizations"""
        queryset = super().get_queryset()
        
        queryset = queryset.select_related('account', 'category')
        
        return queryset

    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get transaction summary statistics"""
        queryset = self.filter_queryset(self.get_queryset())
        
        total_count = queryset.count()
        income_total = queryset.filter(transaction_type='income').aggregate(
            total=Sum('amount'))['total'] or 0
        expense_total = queryset.filter(transaction_type='expense').aggregate(
            total=Sum('amount'))['total'] or 0
        
        return Response({
            'total_transactions': total_count,
            'total_income': income_total,
            'total_expenses': expense_total,
            'net_amount': income_total - expense_total,
            'date_range': {
                'earliest': queryset.aggregate(Min('date'))['date__min'],
                'latest': queryset.aggregate(Max('date'))['date__max'],
            }
        })

    @action(detail=False, methods=['get'])
    def export(self, request):
        """Export filtered transactions as CSV"""
        import csv
        from django.http import HttpResponse
        
        queryset = self.filter_queryset(self.get_queryset())
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="transactions.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'Date', 'Description', 'Amount', 'Type', 'Category', 
            'Account', 'Method'
        ])
        
        for transaction in queryset:
            writer.writerow([
                transaction.date,
                transaction.description,
                transaction.amount,
                transaction.transaction_type,
                transaction.category.name if transaction.category else '',
                transaction.account.account_number if transaction.account else '',
                transaction.method or ''
            ])
        
        return response

    @action(detail=False, methods=['get'])
    def fields(self, request):
        """Get available fields for field selection"""
        serializer = self.get_serializer(context=self.get_serializer_context())
        return Response({
            'available_fields': list(serializer.fields.keys()),
            'required_fields': ['id', 'date', 'amount', 'transaction_type'],
            'computed_fields': ['formatted_amount', 'age_days'],
            'related_fields': ['account_details', 'category_name', 'account_number', 'account_type']
        })

class AccountViewSet(UserScopedViewSet):
    queryset = Account.objects.all()
    serializer_class = AccountSerializer

class CategoryViewSet(UserScopedViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer

class SubscriptionViewSet(UserScopedViewSet):
    queryset = Subscription.objects.all()
    serializer_class = SubscriptionSerializer

class BudgetViewSet(UserScopedViewSet):
    queryset = Budget.objects.all().select_related('category')
    serializer_class = BudgetSerializer

class CustomNotificationViewSet(UserScopedViewSet):
    queryset = CustomNotification.objects.all()
    serializer_class = CustomNotificationSerializer

    @action(detail=False, methods=['get'], url_path='check')
    def check_due_notifications(self, request):
        """
        Checks for due notifications, sends them, and reschedules recurring ones.
        Accessible via GET /api/notifications/check/
        """
        now = datetime.now(tz=ZoneInfo('localtime'))
        
        # Find notifications that are enabled and whose time is due
        due_notifications = self.get_queryset().filter(
            enabled=True,
            notification_datetime__isnull=False,
            notification_datetime__lte=now
        )
        

        if not due_notifications.exists():
            return Response([])

        notifications_to_send = []
        
        for notif in due_notifications:
            notifications_to_send.append(notif)

            # Reschedule or disable based on recurrence
            if notif.recurrence_interval == 'NONE' or notif.recurrence_interval is None:
                # It's a one-time notification, so disable it after sending
                notif.enabled = False
            else:
                # It's a recurring notification - calculate next occurrence
                next_due = notif.notification_datetime
                
                # Ensure the next due time is in the future
                while next_due <= now:
                    if notif.recurrence_interval == 'DAILY':
                        next_due += timedelta(days=1)
                    elif notif.recurrence_interval == 'WEEKLY':
                        next_due += timedelta(weeks=1)
                    elif notif.recurrence_interval == 'MONTHLY':
                        next_due += timedelta(days=30)
                    elif notif.recurrence_interval == 'YEARLY':
                        next_due += timedelta(days=365)
                    else:
                        # Unknown interval, disable to prevent issues
                        notif.enabled = False
                        break
                
                if notif.enabled:
                    notif.notification_datetime = next_due
            
            notif.save()

        serializer = self.get_serializer(notifications_to_send, many=True)
        return Response(serializer.data)



class DashboardViewSet(viewsets.ViewSet):
    """
    ViewSet for aggregated dashboard data
    """
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=False, methods=['get'])
    def summary(self, request):
        """
        Get complete dashboard summary data
        """
        user = request.user
        filters = self._extract_filters(request)
        
        # Get filtered transactions
        transactions_qs = self._get_filtered_transactions(user, filters)
        
        # Calculate financial summary
        financial_summary = self._calculate_financial_summary(transactions_qs)
        
        # Get accounts
        accounts_data = self._get_accounts_data(user)
        
        # Get recent transactions
        recent_transactions = self._get_recent_transactions(transactions_qs)
        
        # Get chart data
        chart_data = self._get_chart_data(transactions_qs)
        
        # Get budget data
        budgets_data = self._get_budgets_data(user, transactions_qs)
        
        # Get subscriptions data
        subscriptions_data = self._get_subscriptions_data(user)
        
        return Response({
            'status': 'success',
            'data': {
                'financial_summary': financial_summary,
                'accounts': accounts_data,
                'recent_transactions': recent_transactions,
                'chart_data': chart_data,
                'budgets': budgets_data,
                'subscriptions': subscriptions_data
            }
        })

    def _extract_filters(self, request):
        """Extract and validate filters from request"""
        return {
            'type': request.GET.get('type'),
            'category': request.GET.get('category'),
            'start_date': request.GET.get('start'),
            'end_date': request.GET.get('end'),
            'account': request.GET.get('account')
        }

    def _get_filtered_transactions(self, user, filters):
        """Get transactions with applied filters"""
        qs = Transaction.objects.filter(user=user).select_related('category', 'account')
        
        if filters['type']:
            qs = qs.filter(transaction_type=filters['type'])
            
        if filters['category']:
            qs = qs.filter(category_id=filters['category'])
            
        if filters['start_date']:
            try:
                start_date = datetime.strptime(filters['start_date'], '%Y-%m-%d').date()
                qs = qs.filter(date__gte=start_date)
            except ValueError:
                pass
                
        if filters['end_date']:
            try:
                end_date = datetime.strptime(filters['end_date'], '%Y-%m-%d').date()
                qs = qs.filter(date__lte=end_date)
            except ValueError:
                pass
                
        if filters['account']:
            qs = qs.filter(account_id=filters['account'])
            
        return qs.order_by('-date')

    def _calculate_financial_summary(self, transactions_qs):
        """Calculate financial summary totals"""
        income_total = transactions_qs.filter(
            transaction_type='income'
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        expense_total = transactions_qs.filter(
            transaction_type='expense'
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        account_count = Account.objects.filter(user=transactions_qs.first().user if transactions_qs.exists() else self.request.user).count()
        
        return {
            'total_income': float(income_total),
            'total_expenses': float(expense_total),
            'net_balance': float(income_total - expense_total),
            'account_count': account_count
        }

    def _get_accounts_data(self, user):
        """Get user's accounts data"""
        accounts = Account.objects.filter(user=user)
        return [
            {
                'id': acc.id,
                'account_number': acc.account_number,
                'account_type': acc.account_type,
                'balance': float(acc.balance)
            }
            for acc in accounts
        ]

    def _get_recent_transactions(self, transactions_qs):
        """Get recent transactions (limited to 10)"""
        recent = transactions_qs[:10]
        return [
            {
                'id': t.id,
                'description': t.description,
                'amount': float(t.amount),
                'type': t.transaction_type,
                'date': t.date.strftime('%Y-%m-%d'),
                'category': t.category.name if t.category else 'Uncategorized',
                'account': t.account.account_number if t.account else 'N/A'
            }
            for t in recent
        ]

    def _get_chart_data(self, transactions_qs):
        """Calculate monthly chart data"""
        monthly_data = {}
        
        for transaction in transactions_qs:
            month_key = transaction.date.strftime('%Y-%m')
            month_display = transaction.date.strftime('%b %Y')
            
            if month_key not in monthly_data:
                monthly_data[month_key] = {
                    'month': month_display,
                    'income': 0,
                    'expenses': 0
                }
            
            if transaction.transaction_type == 'income':
                monthly_data[month_key]['income'] += float(transaction.amount)
            else:
                monthly_data[month_key]['expenses'] += float(transaction.amount)
        
        # Sort by month and get last 6 months
        sorted_months = sorted(monthly_data.items())[-6:]
        
        return {
            'monthly_data': [data for _, data in sorted_months]
        }

    def _get_budgets_data(self, user, transactions_qs):
        """Calculate budget data with spending analysis"""
        budgets = Budget.objects.filter(user=user).select_related('category')
        today = timezone.now().date()
        
        total_budget_amount = 0
        total_spent = 0
        budget_items = []
        
        for budget in budgets:
            # Calculate period dates
            if budget.period == 'monthly':
                period_start = today.replace(day=1)
                if today.month == 12:
                    period_end = today.replace(year=today.year + 1, month=1, day=1) - timedelta(days=1)
                else:
                    period_end = today.replace(month=today.month + 1, day=1) - timedelta(days=1)
            elif budget.period == 'weekly':
                period_start = today - timedelta(days=today.weekday())
                period_end = period_start + timedelta(days=6)
            else:  # yearly
                period_start = today.replace(month=1, day=1)
                period_end = today.replace(month=12, day=31)
            
            # Calculate spent amount for this budget's category in the period
            spent = transactions_qs.filter(
                category=budget.category,
                transaction_type='expense',
                date__gte=period_start,
                date__lte=period_end
            ).aggregate(total=Sum('amount'))['total'] or 0
            
            amount = float(budget.amount)
            spent = float(spent)
            percentage_used = (spent / amount) * 100 if amount > 0 else 0
            remaining = amount - spent
            
            total_budget_amount += amount
            total_spent += spent
            
            budget_items.append({
                'id': budget.id,
                'category_name': budget.category.name,
                'amount': amount,
                'spent': spent,
                'remaining': remaining,
                'percentage_used': round(percentage_used, 1),
                'period': budget.get_period_display(),
                'status': 'over' if spent > amount else 'warning' if percentage_used > 80 else 'good'
            })
        
        return {
            'total_budget_amount': total_budget_amount,
            'total_spent': total_spent,
            'budget_items': budget_items,
            'budget_count': len(budget_items)
        }

    def _get_subscriptions_data(self, user):
        """Get subscriptions summary data"""
        subscriptions = Subscription.objects.filter(user=user)
        active_subscriptions = subscriptions.filter(is_active=True)
        
        # Get next due subscription
        next_due = active_subscriptions.order_by('next_payment_date').first()
        
        return {
            'total': subscriptions.count(),
            'active': active_subscriptions.count(),
            'next_due_date': next_due.next_payment_date.isoformat() if next_due and next_due.next_payment_date else None,
            'next_due_name': next_due.name if next_due else None
        }



'''
@login_required
@require_GET
def spreadsheet_data_api(request):
    """
    Returns all spreadsheet data as JSON for AJAX loading.
    """
    user = request.user
    accounts = Account.objects.filter(user=user)
    categories = Category.objects.filter(user=user)
    transactions = Transaction.objects.filter(user=user).select_related('account', 'category').order_by('-date', '-id')

    accounts_json = [
        {
            'id': acc.id,
            'account_number': acc.account_number,
            'account_type': acc.account_type,
            'balance': float(acc.balance)
        } for acc in accounts
    ]
    categories_json = list(categories.values('id', 'name', 'type'))
    transaction_types_json = [{'id': 'expense', 'name': 'Expense'}, {'id': 'income', 'name': 'Income'}]
    initial_data_json = [
        {
            'id': t.id,
            'date': t.date.strftime('%Y-%m-%d') if t.date else None,
            'account_id': t.account.id if t.account else None,
            'account_name': f"{t.account.account_type} ({t.account.account_number})" if t.account else "",
            'category_name': t.category.name if t.category else None,
            'category_id': t.category.id if t.category else None,
            'description': t.description,
            'amount': float(t.amount) if t.amount is not None else None,
            'transaction_type_name': t.get_transaction_type_display(),
            'transaction_type': t.transaction_type
        }
        for t in transactions
    ]
    return JsonResponse({
        'accounts': accounts_json,
        'categories': categories_json,
        'transaction_types': transaction_types_json,
        'transactions': initial_data_json,
    })

@login_required
@require_POST
def spreadsheet_save_api(request):
    """
    Handles saving spreadsheet data via AJAX.
    """
    try:
        data = json.loads(request.body)
        transactions_to_create = []
        transactions_to_update = []
        updated_transaction_ids = [] 
        errors = []
        created_transactions_data = []

        for i, row_data in enumerate(data):
            if not row_data or not row_data.get('date') or row_data.get('amount') is None:
                if row_data.get('id') and not (row_data.get('date') or row_data.get('amount') is not None):
                    pass
                elif not row_data.get('id') and not (row_data.get('date') or row_data.get('amount') is not None):
                    continue
                else:
                    errors.append(f"Row {i+1}: Missing required fields (date, amount).")
                    continue
            
            transaction_id = row_data.get('id')
            try:
                account_id = row_data.get('account_id')
                category_id = row_data.get('category_id')
                account = Account.objects.get(id=account_id, user=request.user) if account_id else None
                category = Category.objects.get(id=category_id, user=request.user) if category_id else None
                transaction_date_str = row_data.get('date')
                if isinstance(transaction_date_str, str):
                    try:
                        transaction_date = datetime.strptime(transaction_date_str, '%Y-%m-%d').date()
                    except ValueError:
                        errors.append(f"Row {i+1}: Invalid date format '{transaction_date_str}'. Expected YYYY-MM-DD.")
                        continue
                else:
                    transaction_date = transaction_date_str

                description = row_data.get('description', '')
                amount = Decimal(row_data.get('amount'))
                transaction_type = row_data.get('transaction_type', 'expense').lower()

                if transaction_id:
                    updated_transaction_ids.append(transaction_id)
                    try:
                        t_instance = Transaction.objects.get(id=transaction_id, user=request.user)
                        if (str(t_instance.date) != str(transaction_date) or
                            t_instance.account_id != account_id or
                            t_instance.category_id != category_id or
                            t_instance.description != description or
                            t_instance.amount != amount or
                            t_instance.transaction_type != transaction_type):
                            if t_instance.account:
                                if t_instance.transaction_type == "income":
                                    t_instance.account.balance -= t_instance.amount
                                else:
                                    t_instance.account.balance += t_instance.amount
                            t_instance.date = transaction_date
                            t_instance.account = account
                            t_instance.category = category
                            t_instance.description = description
                            t_instance.amount = amount
                            t_instance.transaction_type = transaction_type
                            transactions_to_update.append(t_instance) 
                    except Transaction.DoesNotExist:
                        errors.append(f"Row {i+1}: Transaction ID '{transaction_id}' not found for update.")
                        continue
                else:
                    transactions_to_create.append(Transaction(
                        user=request.user, date=transaction_date, account=account, category=category,
                        description=description, amount=amount, transaction_type=transaction_type
                    ))

            except Account.DoesNotExist:
                errors.append(f"Row {i+1}: Account ID '{account_id}' not found or does not belong to you.")
            except Category.DoesNotExist:
                errors.append(f"Row {i+1}: Category ID '{category_id}' not found or does not belong to you.")
            except (ValueError, TypeError) as e:
                errors.append(f"Row {i+1}: Invalid data - {str(e)} for data: {row_data}")
            except Exception as e:
                errors.append(f"Row {i+1}: An unexpected error occurred processing this row - {str(e)}")

        if errors:
            return JsonResponse({'status': 'error', 'errors': errors}, status=400)

        created_count = 0
        if transactions_to_create:
            for t_new in transactions_to_create:
                t_new.save()
                created_count += 1
                created_transactions_data.append({
                    'id': t_new.id,
                    'date': t_new.date.strftime('%Y-%m-%d') if hasattr(t_new.date, 'strftime') else str(t_new.date),
                    'amount': float(t_new.amount),
                    'description': t_new.description
                })

        updated_count = 0
        if transactions_to_update:
            for t_upd in transactions_to_update:
                t_upd.save()
                updated_count += 1

        message_parts = []
        if created_count > 0:
            message_parts.append(f"{created_count} new transaction(s) saved.")
        if updated_count > 0:
            message_parts.append(f"{updated_count} transaction(s) updated.")
        if not message_parts:
            final_message = "No changes detected or no valid transactions to save."
        else:
            final_message = " ".join(message_parts)

        return JsonResponse({
            'status': 'success', 
            'message': final_message,
            'created_transactions': created_transactions_data
        })

    except json.JSONDecodeError:
        return JsonResponse({'status': 'error', 'message': 'Invalid JSON data.'}, status=400)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': f'An unexpected error occurred: {str(e)}'}, status=500)

@login_required
@require_POST
def spreadsheet_delete_api(request):
    """
    Handles deleting transactions via AJAX.
    """
    try:
        data = json.loads(request.body)
        ids = data.get('transaction_ids', [])
        if not ids:
            return JsonResponse({'status': 'error', 'message': 'No transaction IDs provided.'}, status=400)
        transactions = Transaction.objects.filter(id__in=ids, user=request.user)
        count = transactions.count()
        transactions.delete()
        return JsonResponse({'status': 'success', 'message': f'{count} transaction(s) deleted.'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': f'An error occurred: {str(e)}'}, status=500)

@login_required
def subscriptions_api(request):
    user = request.user
    subscriptions = Subscription.objects.filter(user=user, is_active=True)
    today = date.today()
    preview = []
    for sub in subscriptions:
        # Recalculate next payment date if needed
        if sub.next_payment_date < today:
            sub.calculate_next_payment_date()
            sub.save(update_fields=['next_payment_date'])
        preview.append({
            'name': sub.name,
            'amount': float(sub.amount),
            'next_payment_date': sub.next_payment_date.isoformat(),
        })
    
    #get next due subscription
    next_due_sub = min(subscriptions, key=lambda s: s.next_payment_date, default=None)
    data = {
        'total': subscriptions.count(),
        'next_due_date': next_due_sub.next_payment_date.isoformat() if next_due_sub else None,
        'next_due_name': next_due_sub.name if next_due_sub else None,
        'preview': sorted(preview, key=lambda s: s['next_payment_date'])[:5],
    }
    return JsonResponse({'status': 'success', 'data': data})
    '''