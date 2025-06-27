from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST, require_http_methods, require_GET
from .models import Transaction, Account, Category, Subscription, Budget, CustomNotification
from .forms import TransactionForm, CSVUploadForm, BankAccountForm, CategoryForm, UserCreationForm, TransactionQueryForm, AccountManagementForm, SubscriptionForm, BudgetForm, CustomNotificationForm, DateRangeForm
from django.contrib.auth import login, update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib import messages
from datetime import date, timedelta
from collections import defaultdict
from django.db.models import Sum, Q
from django.db.models.functions import TruncMonth
from decimal import Decimal
from django.utils import timezone
from django.http import JsonResponse
from django.core.paginator import Paginator
from datetime import datetime
from django.db.models import Count
import json
import calendar





def landing(request):
    """
    Renders the landing page of the application.

    Args:
        request (HttpRequest): The HTTP request object.

    Returns:
        HttpResponse: The rendered landing page.
    """
    return render(request, 'finance_tracker/landing.html')


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


@login_required
@require_http_methods(["GET"])
def dashboard_api(request):
    """
    Modern API endpoint for dashboard data - returns JSON only
    """
    try:
        user = request.user
        today = timezone.now().date()
        
        # Get transactions with basic filtering
        transactions = Transaction.objects.filter(user=user).order_by('-date')
        
        # Apply any filters from query params
        tx_type = request.GET.get("type")
        if tx_type in ("income", "expense"):
            transactions = transactions.filter(transaction_type=tx_type)
        
        category_id = request.GET.get("category")
        if category_id:
            transactions = transactions.filter(category_id=category_id)
        
        start_date = request.GET.get("start")
        if start_date:
            transactions = transactions.filter(date__gte=start_date)
        
        end_date = request.GET.get("end")
        if end_date:
            transactions = transactions.filter(date__lte=end_date)

        # Calculate totals
        total_income = transactions.filter(transaction_type='income').aggregate(
            total=Sum('amount'))['total'] or 0
        total_expenses = transactions.filter(transaction_type='expense').aggregate(
            total=Sum('amount'))['total'] or 0
        
        # Get recent transactions (limit for performance)
        recent_transactions = transactions[:10]
        
        # Get accounts
        accounts = Account.objects.filter(user=user)
        
        # Calculate monthly data (last 6 months for performance)
        monthly_data = []
        for i in range(6):
            month_start = (today.replace(day=1) - timedelta(days=i*30)).replace(day=1)
            if month_start.month == 12:
                month_end = month_start.replace(year=month_start.year + 1, month=1)
            else:
                month_end = month_start.replace(month=month_start.month + 1)
            
            month_income = Transaction.objects.filter(
                user=user, transaction_type='income',
                date__gte=month_start, date__lt=month_end
            ).aggregate(total=Sum('amount'))['total'] or 0
            
            month_expenses = Transaction.objects.filter(
                user=user, transaction_type='expense',
                date__gte=month_start, date__lt=month_end
            ).aggregate(total=Sum('amount'))['total'] or 0
            
            monthly_data.append({
                'month': month_start.strftime('%b %Y'),
                'income': float(month_income),
                'expenses': float(month_expenses),
                'net': float(month_income - month_expenses)
            })
        
        monthly_data.reverse()

        # Subscriptions data
        subscriptions = Subscription.objects.filter(user=user)
        active_subs = subscriptions.filter(is_active=True)
        total_subs = subscriptions.count()
        active_count = active_subs.count()
        next_due = active_subs.order_by('next_payment_date').first()
        next_due_date = next_due.next_payment_date if next_due else None
        next_due_name = next_due.name if next_due else None

        # Budgets data
        budgets = Budget.objects.filter(user=user).select_related('category')
        budget_data = []
        total_budget_amount = 0
        total_spent_against_budgets = 0
        
        for budget in budgets:
            # Calculate spent amount for this budget's category
            if budget.period == 'monthly':
                period_start = today.replace(day=1)
                period_end = (period_start.replace(month=period_start.month % 12 + 1, day=1) - timedelta(days=1)) if period_start.month < 12 else period_start.replace(year=period_start.year + 1, month=1, day=1) - timedelta(days=1)
            elif budget.period == 'weekly':
                period_start = today - timedelta(days=today.weekday())
                period_end = period_start + timedelta(days=6)
            else:  # yearly
                period_start = today.replace(month=1, day=1)
                period_end = today.replace(month=12, day=31)
            
            spent = Transaction.objects.filter(
                user=user,
                category=budget.category,
                transaction_type='expense',
                date__gte=period_start,
                date__lte=period_end
            ).aggregate(total=Sum('amount'))['total'] or 0
            
            percentage_used = (float(spent) / float(budget.amount)) * 100 if budget.amount > 0 else 0
            remaining = float(budget.amount) - float(spent)
            
            budget_data.append({
                'id': budget.id,
                'category_name': budget.category.name,
                'amount': float(budget.amount),
                'spent': float(spent),
                'remaining': remaining,
                'percentage_used': round(percentage_used, 1),
                'period': budget.get_period_display(),
                'status': 'over' if spent > budget.amount else 'warning' if percentage_used > 80 else 'good'
            })
            
            total_budget_amount += float(budget.amount)
            total_spent_against_budgets += float(spent)


        # Prepare response data
        response_data = {
            'status': 'success',
            'data': {
                'financial_summary': {
                    'total_income': float(total_income),
                    'total_expenses': float(total_expenses),
                    'net_balance': float(total_income - total_expenses),
                    'account_count': accounts.count()
                },
                'accounts': [
                    {
                        'id': acc.id,
                        'account_number': acc.account_number,
                        'account_type': acc.account_type,
                        'balance': float(acc.balance)
                    } for acc in accounts
                ],
                'budgets': {
                    'total_budget_amount': total_budget_amount,
                    'total_spent': total_spent_against_budgets,
                    'budget_items': budget_data,
                    'budget_count': len(budget_data)
                },
                'recent_transactions': [
                    {
                        'id': t.id,
                        'description': t.description,
                        'amount': float(t.amount),
                        'type': t.transaction_type,
                        'date': t.date.strftime('%Y-%m-%d'),
                        'category': t.category.name if t.category else 'Uncategorized',
                        'account': t.account.account_number
                    } for t in recent_transactions
                ],
                'chart_data': {
                    'monthly_data': monthly_data,
                },
                'subscriptions': {
                    'total': total_subs,
                    'active': active_count,
                    'next_due_date': next_due_date.isoformat() if next_due_date else None,
                    'next_due_name': next_due_name,
                },
            }
        }
        return JsonResponse(response_data)
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)
    
@login_required
def dashboard(request):
    """
    Simplified dashboard view - mainly renders template
    AJAX will handle data loading
    """
    # Only get essential data for initial page load
    user = request.user
    categories = Category.objects.filter(user=user)
    
    # Get any flash messages or session data
    show_notification = request.session.get('show_large_transaction_notification', False)
    if show_notification:
        del request.session['show_large_transaction_notification']
    
    context = {
        'categories': categories,  # For filter dropdown
        'show_notification': show_notification,
    }
    
    return render(request, 'finance_tracker/dashboard.html', context)

@login_required
def add_transaction(request):
    """
    Handles the creation of a single manually entered new transaction for the logged-in user.

    - If the request method is POST, validates the submitted form data and saves the transaction.
    - If the request method is GET, displays an empty form for the user to fill out.

    Args:
        request (HttpRequest): The HTTP request object.

    Returns:
        HttpResponse: The rendered add transaction page with the form.
        HttpResponseRedirect: Redirects to the dashboard if the transaction is successfully added.
    """
    initial = {}
    if 'date' in request.GET:
        initial['date'] = request.GET['date']
    
    next_url = request.GET.get('next') or request.POST.get('next')

    if request.method == 'POST':
        
        form = TransactionForm(request.POST, user=request.user)
        if form.is_valid():
            transaction = form.save(commit=False)
            transaction.user = request.user
            transaction.save()
            messages.success(request, "Transaction added successfully!")

            try:
                threshold = float(request.POST.get('transaction_threshold', 100))
            except ValueError:
                threshold = 100
            if float(transaction.amount) >= threshold:
                request.session['show_large_transaction_notification'] = {
                    'amount': float(transaction.amount),
                    'description': transaction.description,
                    'id': transaction.id
                }
            
            if next_url:
                return redirect(next_url)
            return redirect('dashboard')
    else:
        form = TransactionForm(user=request.user, initial=initial)
    return render(request, 'finance_tracker/add_transaction.html', {'form': form, 'next': next_url})
    

def register(request):
    """
    Handles user registration.

    - If the request method is POST, validates the submitted form data and creates a new user.
    - If the request method is GET, displays the registration form.

    Args:
        request (HttpRequest): The HTTP request object.

    Returns:
        HttpResponse: The rendered registration page with the form.
        HttpResponseRedirect: Redirects to the dashboard if registration is successful.
    """
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data["password"])
            user.save()
            login(request, user)
            messages.success(request, "Registration successful! Welcome to your dashboard.")
            return redirect("dashboard")
        else:
            print(f'Invalid form: {form.errors}')
            messages.error(request, "Error registering user. Please try again.")
    else:
        form = UserCreationForm()
    return render(request, 'finance_tracker/register.html', {'form': form})


@login_required
def update_transaction(request, transaction_id):
    """
    Handles updating an existing transaction for the logged-in user.

    - If the request method is POST, validates the submitted form data and updates the transaction.
    - If the request method is GET, displays the form pre-filled with the transaction's current data.

    Args:
        request (HttpRequest): The HTTP request object.
        transaction_id (int): The ID of the transaction to update.

    Returns:
        HttpResponse: The rendered update transaction page with the form.
        HttpResponseRedirect: Redirects to the dashboard if the transaction is successfully updated.
    """
    transaction = get_object_or_404(Transaction, id=transaction_id, user=request.user)
    next_url = request.GET.get('next') or request.POST.get('next')

    if request.method == 'POST':
        form = TransactionForm(request.POST, instance=transaction)
        if form.is_valid():
            form.save()
            if next_url:
                return redirect(next_url)
            return redirect('dashboard')
        else:
            messages.error(request, "Error updating transaction. Please try again.")
    else:
        form = TransactionForm(instance=transaction)

    return render(request, 'finance_tracker/update_transaction.html', {'form': form, 'transaction': transaction, 'next': next_url})




@login_required
def delete_transactions(request):
    """
    Handles the deletion of one or more transactions for the logged-in user.
    """
    if request.method == 'POST':
        is_ajax_json_request = request.content_type == 'application/json' or \
            (hasattr(request, 'headers') and request.headers.get('x-requested-with') == 'XMLHttpRequest')
        
        try:
            transaction_ids = []
            if is_ajax_json_request:
                if request.content_type == 'application/json':
                    data = json.loads(request.body)
                    transaction_ids = data.get('transaction_ids', [])
                else:
                    # Handle URL-encoded AJAX requests
                    transaction_ids = request.POST.getlist('transaction_ids')
                    if not transaction_ids:
                        # Try single value fallback
                        single_id = request.POST.get('transaction_ids')
                        if single_id:
                            transaction_ids = [single_id]
            else:
                transaction_ids = request.POST.getlist('transaction_ids')

            if not transaction_ids:
                message = 'No transactions selected for deletion.'
                if is_ajax_json_request:
                    return JsonResponse({'status': 'error', 'message': message}, status=400)
                else:
                    messages.error(request, message)
                    return redirect('dashboard')

            # Ensure all provided IDs are integers
            try:
                processed_transaction_ids = [int(tid) for tid in transaction_ids]
            except ValueError:
                message = 'Invalid transaction ID format.'
                if is_ajax_json_request:
                    return JsonResponse({'status': 'error', 'message': message}, status=400)
                else:
                    messages.error(request, message)
                    return redirect('dashboard')

            transactions = Transaction.objects.filter(id__in=processed_transaction_ids, user=request.user)
            count = 0
            
            for t in list(transactions): 
                t.delete()
                count += 1
            
            if count > 0:
                message = f"{count} transaction(s) deleted successfully!"
                if is_ajax_json_request:
                    return JsonResponse({'status': 'success', 'message': message})
                else:
                    messages.success(request, message)
                    return redirect('dashboard')
            else:
                message = 'No valid transactions found to delete.'
                if is_ajax_json_request:
                    return JsonResponse({'status': 'error', 'message': message}, status=404)
                else:
                    messages.warning(request, message)
                    return redirect('dashboard')
        
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON format.'}, status=400)
        except Exception as e:
            error_message = f'An unexpected error occurred: {str(e)}'
            if is_ajax_json_request:
                return JsonResponse({'status': 'error', 'message': error_message}, status=500)
            else:
                messages.error(request, error_message)
                return redirect('dashboard')
        
    # For GET or other methods
    if request.content_type == 'application/json' or \
       (hasattr(request, 'headers') and request.headers.get('x-requested-with') == 'XMLHttpRequest'):
        return JsonResponse({'status': 'error', 'message': 'Invalid request method. Only POST is allowed for this operation.'}, status=405)
    else:
        messages.error(request, "Invalid request. This action requires a POST.")
        return redirect(request.META.get('HTTP_REFERER', 'dashboard'))


@login_required
def upload_transactions(request):
    """
    Handles the upload of transactions via a CSV file for the logged-in user.

    - If the request method is POST, processes the uploaded CSV file, validates each row, and saves the transactions if
       they are all valid.
    - Displays error messages for invalid rows or issues with the file.

    Args:
        request (HttpRequest): The HTTP request object.

    Returns:
        HttpResponse: The rendered upload transactions page with the form.
        HttpResponseRedirect: Redirects to the dashboard after processing the file.
    """
    if request.method == "POST":
        form = CSVUploadForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            # Create transactions from validated rows
            count = 0
            for row in form.validated_rows:
                row['amount'] = Decimal(row['amount'])  # Ensure amount is a Decimal
                Transaction.objects.create(
                    user=request.user,
                    **row #unpack the dictionary into the model fields
                )
                count += 1

            messages.success(request, f"{count} transactions uploaded successfully!") if count > 1 else messages.success(request, "Transaction uploaded successfully!")
            return redirect("dashboard")
        else:
            messages.error(request, "Errors present in CSV. Please review the issues below:")
            for error in form.errors.get("__all__", []):
                messages.error(request, error)
    else:
        form = CSVUploadForm(user=request.user)

    return render(request, "finance_tracker/upload_transactions.html", {"form": form})
    

@login_required
def manage_bank_accounts(request):
    """
    Displays a page where users can view, add, or delete their bank accounts.

    - Handles account deletion if the request method is POST and includes an account_id.
    - Handles account addition if the request method is POST and includes form data.
    - Displays the list of bank accounts and the add account form.

    Args:
        request (HttpRequest): The HTTP request object.

    Returns:
        HttpResponse: The rendered manage bank accounts page.
    """
    accounts = Account.objects.filter(user=request.user)

    if request.method == 'POST':
        # Handle account deletion
        account_id = request.POST.get('account_id')
        if account_id:
            account = get_object_or_404(Account, id=account_id, user=request.user)
            account.delete()
            messages.success(request, "Bank account deleted successfully!")
            return redirect('manage_bank_accounts')

        # Handle account addition
        form = BankAccountForm(request.POST, initial={'user': request.user})
        form.instance.user = request.user 
        if form.is_valid():
            bank_account = form.save(commit=False)
            bank_account.user = request.user
            bank_account.save()
            messages.success(request, "Bank account added successfully!")
            return redirect('manage_bank_accounts')
        else:
            messages.error(request, "Error adding bank account. Please try again.")
    else:
        form = BankAccountForm()

    return render(request, 'finance_tracker/manage_bank_accounts.html', {
        'accounts': accounts,
        'add_account_form': form,
    })


@login_required
def manage_categories(request):
    """
    Displays a page where users can view, add, or delete their categories.

    - Handles category deletion if the request method is POST and includes a category_id.
    - Handles category addition if the request method is POST and includes form data.
    - Displays the list of categories and the add category form.

    Args:
        request (HttpRequest): The HTTP request object.

    Returns:
        HttpResponse: The rendered manage categories page.
    """
    categories = Category.objects.filter(user=request.user)

    if request.method == 'POST':
        # Handle category deletion
        category_id = request.POST.get('category_id')
        if category_id:
            category = get_object_or_404(Category, id=category_id, user=request.user)
            category.delete()
            messages.success(request, "Category deleted successfully!")
            return redirect('manage_categories')

        # Handle category addition
        form = CategoryForm(request.POST)
        form.instance.user = request.user
        if form.is_valid():
            category = form.save(commit=False)
            category.user = request.user
            category.save()
            messages.success(request, "Category added successfully!")
            return redirect('manage_categories')
        else:
            messages.error(request, "Error adding category. Please try again.")
    else:
        form = CategoryForm()

    return render(request, 'finance_tracker/manage_categories.html', {
        'categories': categories,
        'add_category_form': form,
    })


@login_required
def query_transactions(request):
    """
    Handles querying transactions based on user input.

    - Filters transactions based on keyword, date range, amount range, transaction type, and method.
    - Displays the filtered transactions in a table.

    Args:
        request (HttpRequest): The HTTP request object.

    Returns:
        HttpResponse: The rendered query transactions page with the form and results.
    """
    form = TransactionQueryForm(request.GET or None)
    transactions = Transaction.objects.filter(user=request.user)

    if form.is_valid():
        # Keyword Search
        keyword = form.cleaned_data.get("keyword")
        if keyword:
            transactions = transactions.filter(
                Q(description__icontains=keyword) | Q(category__name__icontains=keyword)
            )

        # Date Range
        date_range = form.cleaned_data.get("date_range")
        if date_range == "4weeks":
            transactions = transactions.filter(date__gte=date.today() - timedelta(weeks=4))
        elif date_range == "3m":
            transactions = transactions.filter(date__gte=date.today() - timedelta(weeks=12))
        elif date_range == "6m":
            transactions = transactions.filter(date__gte=date.today() - timedelta(weeks=24))
        elif date_range == "12m":
            transactions = transactions.filter(date__gte=date.today() - timedelta(weeks=48))
        elif date_range == "custom":
            start_date = form.cleaned_data.get("start_date")
            end_date = form.cleaned_data.get("end_date")
            if start_date and end_date:
                transactions = transactions.filter(date__range=(start_date, end_date))


        # Amount Range
        min_amount = form.cleaned_data.get("min_amount")
        max_amount = form.cleaned_data.get("max_amount")
        if min_amount is not None:
            transactions = transactions.filter(amount__gte=min_amount)
        if max_amount is not None:
            transactions = transactions.filter(amount__lte=max_amount)

        # Transaction Type
        transaction_type = form.cleaned_data.get("transaction_type")
        if transaction_type and transaction_type != "all":
            transactions = transactions.filter(transaction_type=transaction_type)
        # Transaction Method
        transaction_method = form.cleaned_data.get("transaction_method")
        if transaction_method and transaction_method != "all":
            transactions = transactions.filter(method=transaction_method)
        

    # Pagination
    transactions = transactions.order_by('-date', '-id')

    paginator = Paginator(transactions, 20)
    page_number = request.GET.get('page')
    transactions_page = paginator.get_page(page_number)
    return render(request, "finance_tracker/query_transactions.html", {
        "form": form,
        "transactions": transactions_page,
    })


@login_required
def manage_account(request):
    """
    Handles account management for the logged-in user.

    - Allows the user to update their account details, change their password, or delete their account.
    - Displays the appropriate forms for each action.
    - If the user deletes their account they are redirected to the landing page, otherwise
      they are redireccted to the manage account page.
    - Displays success or error messages based on the actions taken.

    Args:
        request (HttpRequest): The HTTP request object.

    Returns:
        HttpResponse: The rendered manage account page with the forms.
        HttpResponseRedirect: Redirects to the appropriate page after processing the user's action.
    """

    user = request.user

    if request.method == "POST":
        if "update_account" in request.POST:
            form = AccountManagementForm(request.POST, instance=user)
            password_form = PasswordChangeForm(user)
            if form.is_valid():
                form.save()
                messages.success(request, "Account details updated successfully!")
                return redirect("manage_account")
            else:
                messages.error(request, "Error updating account details. Please try again.")
        elif "change_password" in request.POST:
            form = AccountManagementForm(instance=user)
            password_form = PasswordChangeForm(user, request.POST)
            if password_form.is_valid():
                password_form.save()
                update_session_auth_hash(request, user)  # Prevents logout after password change
                messages.success(request, "Password changed successfully!")
                return redirect("manage_account")
            else:
                messages.error(request, "Error changing password. Please try again.")
        elif "delete_account" in request.POST:
            user.delete()
            messages.success(request, "Your account and all associated data have been deleted.")
            return redirect("landing")
    else:
        form = AccountManagementForm(instance=user)
        password_form = PasswordChangeForm(user)

    return render(request, "finance_tracker/manage_account.html", {
        "form": form,
        "password_form": password_form,
    })


@login_required
def manage_subscriptions(request):
    """
    Displays a page where users can view, add, or delete their subscriptions.

    - Handles subscription deletion if the request method is POST and includes a subscription_id.
    - Handles subscription addition if the request method is POST and includes form data.
    - Displays the list of subscriptions and the add subscription form.

    Args:
        request (HttpRequest): The HTTP request object.

    Returns:
        HttpResponse: The rendered manage subscriptions page.
    """
    subscriptions = Subscription.objects.filter(user=request.user)

    if request.method == 'POST':
        # Handle subscription deletion
        subscription_id = request.POST.get('subscription_id')
        if subscription_id:
            subscription = get_object_or_404(Subscription, id=subscription_id, user=request.user)
            subscription.delete()
            messages.success(request, "Subscription deleted successfully!")
            return redirect('manage_subscriptions')

        # Handle subscription addition
        form = SubscriptionForm(request.POST, user=request.user)
        form.instance.user = request.user
        if form.is_valid():
            subscription = form.save(commit=False)
            subscription.user = request.user
            subscription.save()
            messages.success(request, "Subscription added successfully!")
            return redirect('manage_subscriptions')
        else:
            messages.error(request, "Error adding subscription. Please try again.")
    else:
        form = SubscriptionForm(user=request.user)

    return render(request, 'finance_tracker/manage_subscriptions.html', {
        'subscriptions': subscriptions,
        'add_subscription_form': form,
    })

@login_required
def update_subscription(request, subscription_id):
    """
    Handles updating an existing subscription for the logged-in user.

    Args:
        request (HttpRequest): The HTTP request object.
        subscription_id (int): The ID of the subscription to update.

    Returns:
        HttpResponse: The rendered update subscription page with the form.
        HttpResponseRedirect: Redirects to manage_subscriptions if the subscription is successfully updated.
    """
    subscription = get_object_or_404(Subscription, id=subscription_id, user=request.user)

    if request.method == 'POST':
        form = SubscriptionForm(request.POST, instance=subscription, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Subscription updated successfully!")
            return redirect('manage_subscriptions')
    else:
        form = SubscriptionForm(instance=subscription, user=request.user)

    return render(request, 'finance_tracker/update_subscription.html', {
        'form': form,
        'subscription': subscription
    })


@login_required
@require_POST
def update_theme_preference(request):
    """
    Updates the user's theme preference.
    
    Args:
        request (HttpRequest): The HTTP request containing the theme preference.
        
    Returns:
        JsonResponse: A response indicating whether the operation was successful.
    """
    theme = request.POST.get('theme')
    if theme in ['light', 'dark']:
        request.user.theme = theme
        request.user.save()
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error', 'message': 'Invalid theme'}, status=400)

        
@login_required
def transaction_calendar(request):
    """
    Renders a calendar view of transactions for the logged-in user.
    
    - Prepares transaction data for display in a calendar format
    - Passes the data as JSON for the JavaScript calendar library
    
    Args:
        request (HttpRequest): The HTTP request object.
        
    Returns:
        HttpResponse: The rendered calendar view page.
    """
    transactions = Transaction.objects.filter(user=request.user).select_related('account', 'category').order_by('-date')
    
    # Prepare transaction data for the calendar
    transaction_data = []
    for t in transactions:
        transaction_data.append({
            'id': t.id,
            'date': t.date.strftime('%Y-%m-%d'),
            'description': t.description or f"{t.get_transaction_type_display()} transaction",
            'amount': float(t.amount),
            'transaction_type': t.transaction_type,
            'category_name': t.category.name if t.category else 'Uncategorized',
            'account_number': t.account.account_number if t.account else 'N/A',
            'account_type': t.account.get_account_type_display() if t.account else 'N/A',
            'account_balance': float(t.account.balance) if t.account else 0.0
        })
    
    return render(request, 'finance_tracker/transaction_calendar.html', {
        'transaction_data': transaction_data
    })


@login_required
def transaction_timeline(request):
    """
    Renders a timeline view of transactions for the logged-in user.
    
    - Displays transactions in chronological order in a visual timeline
    
    Args:
        request (HttpRequest): The HTTP request object.
        
    Returns:
        HttpResponse: The rendered timeline view page.
    """
    transactions = Transaction.objects.filter(user=request.user).select_related('account', 'category').order_by('-date')

    transaction_data = []
    for t in transactions:
        transaction_data.append({
            'id': t.id,
            'date': t.date.strftime('%Y-%m-%d'),
            'description': t.description or f"{t.get_transaction_type_display()} transaction",
            'amount': float(t.amount),
            'transaction_type': t.transaction_type,
            'category_name': t.category.name if t.category else 'Uncategorized',
            'account_number': t.account.account_number if t.account else 'N/A',
            'account_type': t.account.get_account_type_display() if t.account else 'N/A',
            'account_balance': float(t.account.balance) if t.account else 0.0
        })
    
    return render(request, 'finance_tracker/transaction_timeline.html', {
        'transactions': transactions,
        'transaction_data': transaction_data,
    })


@login_required
def notification_settings(request):
    """
    Renders the notification settings page.
    
    Allows the user to configure their notification preferences.
    
    Args:
        request (HttpRequest): The HTTP request object.
        
    Returns:
        HttpResponse: The rendered notification settings page.
    """
    custom_notifications_list = CustomNotification.objects.filter(user=request.user).order_by('-created_at')
    
    if request.method == 'POST':
        # Check if this POST request is for the custom notification form
        if 'form_type' in request.POST and request.POST['form_type'] == 'custom_notification':
            custom_form = CustomNotificationForm(request.POST, user=request.user)
            if custom_form.is_valid():
                notif = custom_form.save(commit=False)
                notif.user = request.user
                notif.save()
                messages.success(request, 'Custom notification rule added successfully.')
                return redirect('notification_settings') # Redirect to the same page
            else:
                messages.error(request, 'Please correct the errors in the custom rule form.')
                # Pass the form with errors back to the template
                return render(request, 'finance_tracker/notification_settings.html', {
                    'custom_notification_form': custom_form, # form with errors
                    'custom_notifications_list': custom_notifications_list
                })

    else:
        custom_form = CustomNotificationForm(user=request.user)

    return render(request, 'finance_tracker/notification_settings.html', {
        'custom_notification_form': custom_form,
        'custom_notifications_list': custom_notifications_list
    })


@login_required
def delete_custom_notification(request, notification_id):
    notification = get_object_or_404(CustomNotification, id=notification_id, user=request.user)
    if request.method == 'POST':
        notification.delete()
        messages.success(request, 'Custom notification rule deleted.')
    return redirect('notification_settings')

@login_required
def manage_budgets(request):
    budgets = Budget.objects.filter(user=request.user).select_related('category')
    if request.method == 'POST':
        if 'delete_budget' in request.POST:
            budget_id = request.POST.get('budget_id')
            Budget.objects.filter(id=budget_id, user=request.user).delete()
            messages.success(request, "Budget deleted successfully!")
            return redirect('manage_budgets')
        else:
            form = BudgetForm(request.POST, user=request.user)
            form.instance.user = request.user
            if form.is_valid():
                form.save()
                messages.success(request, "Budget saved successfully!")
                return redirect('manage_budgets')
    else:
        form = BudgetForm(user=request.user)
    return render(request, 'finance_tracker/manage_budgets.html', {
        'budgets': budgets,
        'form': form,
    })


@login_required
def spreadsheet_transactions(request):
    return render(request, 'finance_tracker/spreadsheet_transactions.html')


@login_required
def transaction_heatmap_view(request):
    """
    Renders a page with a calendar heatmap of transaction activity.
    """
    user = request.user
    #one_year_ago = timezone.now().date() - timedelta(days=365)

    # Aggregate transaction counts per day for the last year
    heatmap_transactions_data = Transaction.objects.filter(
        user=user
        #date__gte=one_year_ago
    ).values('date').annotate(
        count=Count('id'),
        total_income=Sum('amount', filter=Q(transaction_type='income')),
        total_expense=Sum('amount', filter=Q(transaction_type='expense'))
    ).order_by('date')

    # Convert to a dictionary format: 
    # {"YYYY-MM-DD": {"count": count, "income": total_income, "expense": total_expense}}
    calendar_heatmap_data = {}
    for item in heatmap_transactions_data:
        date_str = item['date'].strftime('%Y-%m-%d')
        calendar_heatmap_data[date_str] = {
            'count': item['count'],
            'income': float(item['total_income'] or 0),
            'expense': float(item['total_expense'] or 0)
        }

    context = {
        'calendar_heatmap_data_json': calendar_heatmap_data,
    }
    
    return render(request, 'finance_tracker/visualizations/heatmap.html', context)

@login_required
def visualization_hub(request):
    """
    Main hub for all financial data visualizations.
    Provides links to different visualization types.
    """
    return render(request, 'finance_tracker/visualization_hub.html')

@login_required
def sankey_visualization(request):
    """
    Money flow visualization using Sankey diagrams.
    """
    user = request.user
    
    # Get user's accounts, categories, and recent transactions
    accounts = Account.objects.filter(user=user)
    categories = Category.objects.filter(user=user)
    transactions = Transaction.objects.filter(user=user).select_related('account', 'category')
    
    # Aggregate data for Sankey
    income_categories = categories.filter(type='income')
    expense_categories = categories.filter(type='expense')
    
    # Calculate flows
    income_flows = []
    for category in income_categories:
        total = transactions.filter(category=category, transaction_type='income').aggregate(
            total=Sum('amount'))['total'] or 0
        if total > 0:
            income_flows.append({
                'category': category.name,
                'amount': float(total),
                'type': 'income'
            })
    
    expense_flows = []
    for category in expense_categories:
        total = transactions.filter(category=category, transaction_type='expense').aggregate(
            total=Sum('amount'))['total'] or 0
        if total > 0:
            expense_flows.append({
                'category': category.name,
                'amount': float(total),
                'type': 'expense'
            })
    
    context = {
        'income_flows': income_flows,
        'expense_flows': expense_flows,
        'accounts': list(accounts.values('id', 'account_number', 'account_type', 'balance')),
        'total_income': sum(flow['amount'] for flow in income_flows),
        'total_expenses': sum(flow['amount'] for flow in expense_flows),
    }
    
    return render(request, 'finance_tracker/visualizations/sankey.html', context)



@login_required
def treemap_visualization(request):
    """
    Prepares data for and renders the treemap visualization of expenses by category.
    """
    user = request.user

    # Get all categories (both income and expense)
    income_categories = Category.objects.filter(user=user, type='income')
    expense_categories = Category.objects.filter(user=user, type='expense')
    
    # Prepare income data
    income_data = []
    total_income = Decimal(0)
    for category in income_categories:
        category_total = Transaction.objects.filter(
            user=user, 
            category=category, 
            transaction_type='income'
        ).aggregate(total=Sum('amount'))['total'] or Decimal(0)
        
        if category_total > 0:
            income_data.append({
                "name": category.name,
                "value": float(category_total),
                "type": "income"
            })
            total_income += category_total
    
    # Prepare expense data
    expense_data = []
    total_expenses = Decimal(0)
    for category in expense_categories:
        category_total = Transaction.objects.filter(
            user=user, 
            category=category, 
            transaction_type='expense'
        ).aggregate(total=Sum('amount'))['total'] or Decimal(0)
        
        if category_total > 0:
            expense_data.append({
                "name": category.name,
                "value": float(category_total),
                "type": "expense"
            })
            total_expenses += category_total
    
    # Combined data structure
    treemap_data = {
        "name": "Transactions",
        "children": [
            {
                "name": "Income",
                "children": income_data,
                "type": "income"
            },
            {
                "name": "Expenses", 
                "children": expense_data,
                "type": "expense"
            }
        ]
    }
    
    context = {
        'treemap_data_json': treemap_data,
        'income_data_json': {"name": "Income", "children": income_data},
        'expense_data_json': {"name": "Expenses", "children": expense_data},
        'total_income': float(total_income),
        'total_expenses': float(total_expenses),
        'net_balance': float(total_income - total_expenses),
    }
    return render(request, 'finance_tracker/visualizations/treemap.html', context)



@login_required
def bar_chart_visualization(request):
    """
    Monthly income vs expenses bar chart visualization.
    """
    user = request.user
    form = DateRangeForm(request.GET or None)
    
    # Get date range
    if form.is_valid():
        start_date, end_date = form.get_date_range()
    else:
        # Default to last 3 months
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=90)
    
    # Filter transactions by date range
    transactions = Transaction.objects.filter(
        user=user,
        date__gte=start_date,
        date__lte=end_date
    )
    
    # Group by month and aggregate
    monthly_data = []
    total_income = 0
    total_expenses = 0
    
    # Get all months in the date range
    current_date = start_date.replace(day=1)  # Start from first day of month
    end_month = end_date.replace(day=1)
    
    while current_date <= end_month:
        # Get next month
        if current_date.month == 12:
            next_month = current_date.replace(year=current_date.year + 1, month=1)
        else:
            next_month = current_date.replace(month=current_date.month + 1)
        
        # Filter transactions for this month
        month_income = transactions.filter(
            transaction_type='income',
            date__gte=current_date,
            date__lt=next_month
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        month_expenses = transactions.filter(
            transaction_type='expense',
            date__gte=current_date,
            date__lt=next_month
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        monthly_data.append({
            'month': current_date.strftime('%b %Y'),
            'income': float(month_income),
            'expenses': float(month_expenses),
            'net': float(month_income - month_expenses)
        })
        
        total_income += float(month_income)
        total_expenses += float(month_expenses)
        
        current_date = next_month
    
    context = {
        'form': form,
        'monthly_data': monthly_data,
        'start_date': start_date,
        'end_date': end_date,
        'total_income': total_income,
        'total_expenses': total_expenses,
        'net_balance': total_income - total_expenses,
    }
    
    return render(request, 'finance_tracker/visualizations/bar_chart.html', context)

@login_required
def line_chart_visualization(request):
    """
    Transaction trend line chart visualization.
    """
    user = request.user
    form = DateRangeForm(request.GET or None)
    
    # Get date range
    if form.is_valid():
        start_date, end_date = form.get_date_range()
    else:
        # Default to last 30 days
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=30)
    
    # Generate daily data
    daily_data = []
    current_date = start_date
    total_period_income = 0
    total_period_expenses = 0
    
    while current_date <= end_date:
        daily_income = Transaction.objects.filter(
            user=user,
            transaction_type='income',
            date=current_date
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        daily_expenses = Transaction.objects.filter(
            user=user,
            transaction_type='expense',
            date=current_date
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        daily_data.append({
            'date': current_date.strftime('%Y-%m-%d'),
            'formatted_date': current_date.strftime('%b %d'),
            'income': float(daily_income),
            'expenses': float(daily_expenses),
            'net': float(daily_income - daily_expenses)
        })
        
        total_period_income += float(daily_income)
        total_period_expenses += float(daily_expenses)
        
        current_date += timedelta(days=1)
    
    net_period_balance = total_period_income - total_period_expenses
    
    context = {
        'form': form,
        'daily_data': daily_data,
        'start_date': start_date,
        'end_date': end_date,
        'date_range': f"{start_date.strftime('%B %d')} - {end_date.strftime('%B %d, %Y')}",
        'total_period_income': total_period_income,
        'total_period_expenses': total_period_expenses,
        'net_period_balance': net_period_balance,
    }
    
    return render(request, 'finance_tracker/visualizations/line_chart.html', context)



@login_required
def pie_chart_visualization(request):
    """
    Income vs expenses pie chart with category breakdowns.
    """
    user = request.user
    form = DateRangeForm(request.GET or None)
    
    # Get date range
    if form.is_valid():
        start_date, end_date = form.get_date_range()
    else:
        # Default to last 3 months
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=90)
    
    # Filter transactions by date range
    transactions = Transaction.objects.filter(
        user=user,
        date__gte=start_date,
        date__lte=end_date
    )
    
    # Get totals
    total_income = transactions.filter(
        transaction_type='income'
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    total_expenses = transactions.filter(
        transaction_type='expense'
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    # Get category breakdowns
    income_categories = transactions.filter(
        transaction_type='income'
    ).values('category__name').annotate(
        total=Sum('amount')
    ).order_by('-total')
    
    expense_categories = transactions.filter(
        transaction_type='expense'
    ).values('category__name').annotate(
        total=Sum('amount')
    ).order_by('-total')
    
    context = {
        'form': form,
        'start_date': start_date,
        'end_date': end_date,
        'total_income': float(total_income),
        'total_expenses': float(total_expenses),
        'net_balance': float(total_income - total_expenses),
        'income_categories': [
            {'name': item['category__name'] or 'Uncategorized', 'amount': float(item['total'])}
            for item in income_categories
        ],
        'expense_categories': [
            {'name': item['category__name'] or 'Uncategorized', 'amount': float(item['total'])}
            for item in expense_categories
        ],
    }
    
    return render(request, 'finance_tracker/visualizations/pie_chart.html', context)



@login_required
def network_visualization(request):
    """
    Network diagram visualization showing relationships between accounts, categories, and transactions.
    """
    user = request.user
    
    # Get user's data
    accounts = Account.objects.filter(user=user)
    categories = Category.objects.filter(user=user)
    transactions = Transaction.objects.filter(user=user).select_related('account', 'category')
    
    # Build nodes (accounts and categories)
    nodes = []
    links = []
    node_id_map = {}
    
    # Add account nodes
    for account in accounts:
        node_id = f"account_{account.id}"
        nodes.append({
            'id': node_id,
            'name': account.account_number,
            'type': 'account',
            'balance': float(account.balance),
            'account_type': account.account_type,
            'size': min(max(float(account.balance) / 100, 10), 50)  # Size based on balance
        })
        node_id_map[f"account_{account.id}"] = len(nodes) - 1
    
    # Add category nodes
    for category in categories:
        node_id = f"category_{category.id}"
        # Calculate total transaction volume for this category
        total_volume = transactions.filter(category=category).aggregate(
            total=Sum('amount'))['total'] or 0
        
        nodes.append({
            'id': node_id,
            'name': category.name,
            'type': 'category',
            'category_type': category.type if hasattr(category, 'type') else 'general',
            'total_volume': float(total_volume),
            'size': min(max(float(total_volume) / 50, 8), 40)  # Size based on volume
        })
        node_id_map[f"category_{category.id}"] = len(nodes) - 1
    
    # Build links (transaction relationships)
    account_category_flows = {}
    
    for transaction in transactions:
        account_id = f"account_{transaction.account.id}"
        category_id = f"category_{transaction.category.id}" if transaction.category else "category_uncategorized"
        
        # Create uncategorized node if needed
        if not transaction.category and category_id not in node_id_map:
            nodes.append({
                'id': category_id,
                'name': 'Uncategorized',
                'type': 'category',
                'category_type': 'general',
                'total_volume': 0,
                'size': 10
            })
            node_id_map[category_id] = len(nodes) - 1
        
        # Track flows between accounts and categories
        flow_key = f"{account_id}:{category_id}"
        if flow_key not in account_category_flows:
            account_category_flows[flow_key] = {
                'source': account_id,
                'target': category_id,
                'total_amount': 0,
                'transaction_count': 0,
                'income_amount': 0,
                'expense_amount': 0
            }
        
        account_category_flows[flow_key]['total_amount'] += float(transaction.amount)
        account_category_flows[flow_key]['transaction_count'] += 1
        
        if transaction.transaction_type == 'income':
            account_category_flows[flow_key]['income_amount'] += float(transaction.amount)
        else:
            account_category_flows[flow_key]['expense_amount'] += float(transaction.amount)
    
    # Convert flows to links
    for flow_key, flow_data in account_category_flows.items():
        if flow_data['total_amount'] > 0:  # Only include flows with actual transactions
            links.append({
                'source': flow_data['source'],
                'target': flow_data['target'],
                'value': flow_data['total_amount'],
                'transaction_count': flow_data['transaction_count'],
                'income_amount': flow_data['income_amount'],
                'expense_amount': flow_data['expense_amount'],
                'width': min(max(flow_data['total_amount'] / 100, 1), 20)  # Link width based on amount
            })
    
    # Calculate network statistics
    total_accounts = len(accounts)
    total_categories = len(categories)
    total_connections = len(links)
    avg_transactions_per_connection = sum(link['transaction_count'] for link in links) / len(links) if links else 0
    
    network_stats = {
        'total_nodes': len(nodes),
        'total_accounts': total_accounts,
        'total_categories': total_categories,
        'total_connections': total_connections,
        'avg_transactions_per_connection': round(avg_transactions_per_connection, 1),
        'most_active_account': max(nodes, key=lambda x: x.get('size', 0) if x['type'] == 'account' else 0)['name'] if any(n['type'] == 'account' for n in nodes) else 'None',
        'most_active_category': max(nodes, key=lambda x: x.get('size', 0) if x['type'] == 'category' else 0)['name'] if any(n['type'] == 'category' for n in nodes) else 'None'
    }
    
    context = {
        'network_data': {
            'nodes': nodes,
            'links': links
        },
        'network_stats': network_stats,
        'total_income': transactions.filter(transaction_type='income').aggregate(total=Sum('amount'))['total'] or 0,
        'total_expenses': transactions.filter(transaction_type='expense').aggregate(total=Sum('amount'))['total'] or 0,
    }
    
    return render(request, 'finance_tracker/visualizations/network.html', context)