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

from .filters import TransactionFilter, AccountFilter, CategoryFilter, BudgetFilter, SubscriptionFilter, CustomNotificationFilter
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

class EnhancedUserScopedViewSet(UserScopedViewSet):
    """
    A base ViewSet that adds pagination, filtering, searching, and ordering
    to the UserScopedViewSet.
    """
    pagination_class = TransactionPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]


# --- ViewSets for each model ---

class TransactionViewSet(EnhancedUserScopedViewSet):
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

class AccountViewSet(EnhancedUserScopedViewSet):
    queryset = Account.objects.all()
    serializer_class = AccountSerializer
    filterset_class = AccountFilter
    search_fields = ['account_number', 'account_type']
    ordering_fields = ['balance', 'account_type', 'created_at']
    ordering = ['-balance']

class CategoryViewSet(EnhancedUserScopedViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    filterset_class = CategoryFilter
    search_fields = ['name']
    ordering_fields = ['name', 'type']
    ordering = ['name']

class SubscriptionViewSet(EnhancedUserScopedViewSet):
    queryset = Subscription.objects.all()
    serializer_class = SubscriptionSerializer
    filterset_class = SubscriptionFilter
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'amount', 'next_payment_date', 'start_date']
    ordering = ['next_payment_date']

class BudgetViewSet(EnhancedUserScopedViewSet):
    queryset = Budget.objects.all().select_related('category')
    serializer_class = BudgetSerializer
    filterset_class = BudgetFilter
    search_fields = ['category__name']
    ordering_fields = ['amount', 'period']
    ordering = ['-amount']

class CustomNotificationViewSet(EnhancedUserScopedViewSet):
    queryset = CustomNotification.objects.all()
    serializer_class = CustomNotificationSerializer
    filterset_class = CustomNotificationFilter
    search_fields = ['title', 'message']
    ordering_fields = ['notification_datetime', 'type', 'created_at']
    ordering = ['-notification_datetime']

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