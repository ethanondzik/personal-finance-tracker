from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from .models import Transaction, Account, Category, Subscription, Budget, CustomNotification
from .forms import TransactionForm, CSVUploadForm, BankAccountForm, CategoryForm, UserCreationForm, TransactionQueryForm, AccountManagementForm, SubscriptionForm, BudgetForm, CustomNotificationForm
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
def dashboard(request):
    """
    Renders the dashboard page for the logged-in user.

    - Displays a list of all transactions for the user, ordered by date.
    - Aggregates income and expenses by date to prepare data for the transactions graph.
    - Passes the transactions and chart data to the template for rendering.

    Args:
        request (HttpRequest): The HTTP request object.

    Returns:
        HttpResponse: The rendered dashboard page with the user's transactions and chart data.
    """

    #Shows all income and all expenses on the same day for each day
    transactions = Transaction.objects.filter(user=request.user).order_by('date')
    accounts = list(Account.objects.filter(user=request.user).values(
        'account_number', 'account_type', 'balance'
    ))
    categories = Category.objects.filter(user=request.user)

    
    #Total income and expenses for the logged-in user
    total_income = transactions.filter(transaction_type='income').aggregate(Sum('amount'))['amount__sum'] or 0
    total_expenses = transactions.filter(transaction_type='expense').aggregate(Sum('amount'))['amount__sum'] or 0

    #Monthly aggregation
    monthly_data = Transaction.objects.filter(user=request.user).annotate(
        month=TruncMonth('date')
    ).values('month').annotate(
        income=Sum('amount', filter=Q(transaction_type='income')),
        expenses=Sum('amount', filter=Q(transaction_type='expense'))
    ).order_by('month')

    # Calculate the total income and expenses for each month
    months = []
    monthly_income = []
    monthly_expenses = []
    for entry in monthly_data:
        months.append(entry['month'].strftime("%b %Y"))
        monthly_income.append(float(entry['income'] or 0))
        monthly_expenses.append(float(entry['expenses'] or 0))

    # Use a dictionary to aggregate income and expenses by date
    aggregated_data = defaultdict(lambda: {"income": 0, "expenses": 0})
    for transaction in transactions:
        date_str = transaction.date.strftime('%Y-%m-%d')
        if transaction.transaction_type == 'income':
            aggregated_data[date_str]["income"] += float(transaction.amount)
        elif transaction.transaction_type == 'expense':
            aggregated_data[date_str]["expenses"] += float(transaction.amount)

    # Sort the dates and prepare the chart data
    sorted_dates = sorted(aggregated_data.keys())
    chart_data = {
        "dates": sorted_dates,
        "income": [aggregated_data[date]["income"] for date in sorted_dates],
        "expenses": [aggregated_data[date]["expenses"] for date in sorted_dates],
        "total_income": float(total_income),
        "total_expenses": float(total_expenses),
        "months": months,
        "monthly_income": monthly_income,
        "monthly_expenses": monthly_expenses,
    }

    today = timezone.now().date()
    
    # Get upcoming subscriptions (due in the next 30 days)
    upcoming_subscriptions = Subscription.objects.filter(
        user=request.user,
        is_active=True,
        next_payment_date__gte=today,
        next_payment_date__lte=today + timedelta(days=30)
    ).order_by('next_payment_date')[:3]  # Limit to 3 most upcoming
    
    # Calculate days until due for each subscription
    for subscription in upcoming_subscriptions:
        delta = subscription.next_payment_date - today
        subscription.days_until = delta.days

    # Filtering logic
    tx_type = request.GET.get("type")
    if tx_type in ("income", "expense"):
        transactions = transactions.filter(transaction_type=tx_type)
    category_id = request.GET.get("category")
    if category_id:
        transactions = transactions.filter(category_id=category_id)
    start = request.GET.get("start")
    if start:
        transactions = transactions.filter(date__gte=start)
    end = request.GET.get("end")
    if end:
        transactions = transactions.filter(date__lte=end)

    budgets = Budget.objects.filter(user=request.user)
    first_of_month = today.replace(day=1)

    budget_data = []
    
    for budget in budgets:
        spent = Transaction.objects.filter(
            user=request.user,
            category=budget.category,
            date__gte=first_of_month,  # for monthly budgets
            date__lte=today,
            transaction_type='expense'
        ).aggregate(total=Sum('amount'))['total'] or 0
        progress = float(spent) / float(budget.amount) if budget.amount else 0
        budget_data.append({
            'id': budget.category.id,
            'name': budget.category.name,
            'budget': float(budget.amount),
            'spent': float(spent),
            'progress': progress * 100,
            'remaining': float(budget.amount) - float(spent),
        })

    # Pagination
    paginator = Paginator(transactions, 20)
    page_number = request.GET.get('page')
    transactions_page = paginator.get_page(page_number)

   
    custom_notifications_data = CustomNotification.objects.filter(user=request.user)
    user_custom_notifications_data = []
    for rule in custom_notifications_data:
        user_custom_notifications_data.append({
            'id': rule.id,
            'title': rule.title,
            'message': rule.message,
            'type': rule.type,
            'threshold': float(rule.threshold) if rule.threshold is not None else None,
            'category_id': rule.category.id if rule.category else None,
            'category_name': rule.category.name if rule.category else None,
            'notification_datetime': rule.notification_datetime.strftime('%Y-%m-%dT%H:%M') if rule.notification_datetime else None,
            'recurrence_interval': rule.recurrence_interval,
            'enabled': rule.enabled,
        })
    
    # Return the rendered template with ALL context data
    response = render(request, 'finance_tracker/dashboard.html', {
        'transactions': transactions_page,
        'chart_data': chart_data,   
        'accounts': accounts,
        'categories': categories,
        'upcoming_subscriptions': upcoming_subscriptions,
        'today': today,
        'budget_data': budget_data,
        'user_custom_notifications': user_custom_notifications_data,
    })

    # Clear the notification flag after rendering
    if 'show_large_transaction_notification' in request.session:
        del request.session['show_large_transaction_notification']
    return response

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

    - If the request method is POST and the user confirms deletion, deletes the selected transactions.
    - If no valid transactions are found, displays an error message.

    Args:
        request (HttpRequest): The HTTP request object.

    Returns:
        HttpResponseRedirect: Redirects to the dashboard after processing the deletion.
    """
    if request.method == 'POST':
        is_ajax_json_request = request.content_type == 'application/json'
        
        try:
            transaction_ids = []
            if is_ajax_json_request:
                data = json.loads(request.body)
                transaction_ids = data.get('transaction_ids', [])
            else: # Standard form post (e.g., from dashboard)
                transaction_ids = request.POST.getlist('transaction_ids')
                # The dashboard form includes a 'confirm' hidden input.
                # For AJAX, confirmation is handled client-side before the request.
                if 'confirm' not in request.POST:
                    messages.error(request, "Deletion not confirmed.")
                    return redirect(request.META.get('HTTP_REFERER', 'dashboard'))

            if not transaction_ids:
                message = 'No transaction IDs provided.'
                if is_ajax_json_request:
                    return JsonResponse({'status': 'error', 'message': message}, status=400)
                else:
                    messages.error(request, message)
                    return redirect(request.META.get('HTTP_REFERER', 'dashboard'))

            # Ensure all provided IDs are integers if they are strings
            try:
                # Filter out empty strings or None before attempting int conversion
                valid_transaction_ids_str = [tid for tid in transaction_ids if tid]
                if not valid_transaction_ids_str: # All IDs were empty or None
                    message = 'No valid transaction IDs provided.'
                    if is_ajax_json_request:
                        return JsonResponse({'status': 'error', 'message': message}, status=400)
                    else:
                        messages.error(request, message)
                        return redirect(request.META.get('HTTP_REFERER', 'dashboard'))
                processed_transaction_ids = [int(tid) for tid in valid_transaction_ids_str]
            except ValueError:
                message = 'Invalid transaction ID format. IDs must be numbers.'
                if is_ajax_json_request:
                    return JsonResponse({'status': 'error', 'message': message}, status=400)
                else:
                    messages.error(request, message)
                    return redirect(request.META.get('HTTP_REFERER', 'dashboard'))

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
                    # For dashboard deletions, redirect back to the dashboard
                    return redirect('dashboard') 
            else:
                message = 'No valid transactions found to delete or you do not own them.'
                if is_ajax_json_request:
                    return JsonResponse({'status': 'error', 'message': message}, status=404)
                else:
                    messages.error(request, message)
                    return redirect(request.META.get('HTTP_REFERER', 'dashboard'))
        
        except json.JSONDecodeError: # This error is specific to AJAX requests with malformed JSON
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON format.'}, status=400)
        except Exception as e:
            # logger.error(f"Error deleting transactions: {str(e)}")
            error_message = f'An unexpected error occurred: {str(e)}'
            if is_ajax_json_request:
                return JsonResponse({'status': 'error', 'message': error_message}, status=500)
            else:
                messages.error(request, error_message)
                return redirect(request.META.get('HTTP_REFERER', 'dashboard'))
        
    # For GET or other methods
    # Distinguish response type for non-POST requests as well
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
        form = SubscriptionForm(request.POST)
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
        form = SubscriptionForm()

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
        form = SubscriptionForm(request.POST, instance=subscription)
        if form.is_valid():
            form.save()
            messages.success(request, "Subscription updated successfully!")
            return redirect('manage_subscriptions')
    else:
        form = SubscriptionForm(instance=subscription)

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
    user = request.user
    accounts = Account.objects.filter(user=user)
    categories = Category.objects.filter(user=user)
    
    accounts_list_for_json = []
    for acc in accounts:
        display_name = str(acc.institution_number) if acc.institution_number else f"Account ending in {acc.account_number[-4:] if acc.account_number and len(acc.account_number) >= 4 else acc.account_number}"
        accounts_list_for_json.append({
            'id': acc.id,
            'name': display_name, 
            'account_number': acc.account_number,
            'account_type': acc.account_type
        })

    # Fetch existing transactions for the user
    existing_transactions = Transaction.objects.filter(user=user).select_related('account', 'category').order_by('-date', '-id')
    
    initial_data_structure = []
    for t in existing_transactions:
        account_name_display = None
        if t.account:
            
            account_name_display = f"{t.account.account_type} ({t.account.account_number})"

        initial_data_structure.append({
            'id': t.id, # for identifying existing transactions
            'date': t.date.strftime('%Y-%m-%d') if t.date else None,
            'account_id': t.account.id if t.account else None,
            'account_name': account_name_display,
            'category_name': t.category.name if t.category else None,
            'description': t.description,
            'amount': float(t.amount) if t.amount is not None else None,
            'transaction_type_name': t.get_transaction_type_display() # 'Income' or 'Expense'
        })

    context = {
        'accounts_json': accounts_list_for_json,
        'categories_json': list(categories.values('id', 'name', 'type')), 
        'transaction_types_json': [{'id': 'expense', 'name': 'Expense'}, {'id': 'income', 'name': 'Income'}],
        'initial_data_json': initial_data_structure,
    }
    return render(request, 'finance_tracker/spreadsheet_transactions.html', context)

@login_required
@require_POST
def save_spreadsheet_transactions(request):
    try:
        data = json.loads(request.body)
        transactions_to_create = []
        transactions_to_update = []
        updated_transaction_ids = [] 
        errors = []
        created_transactions_data = []

        for i, row_data in enumerate(data):
            # received_ids.add(row_data.get('id'))

            # Basic validation and data cleaning
            if not row_data or not row_data.get('date') or row_data.get('amount') is None: # Amount can be 0
                if row_data.get('id') and not (row_data.get('date') or row_data.get('amount') is not None):
                     
                    pass
                elif not row_data.get('id') and not (row_data.get('date') or row_data.get('amount') is not None):
                    # Truly empty new row, skip
                    continue
                else: # Incomplete data for a new or existing row
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

                # from .validation import validate_transaction_data
                # try:
                #     validate_transaction_data({
                #         'date': transaction_date, 'transaction_type': transaction_type, 
                #         'amount': amount, 'description': description, 'category': category
                #     })
                # except ValidationError as e_val:
                #     errors.append(f"Row {i+1}: Validation Error - {', '.join(e_val.messages)}")
                #     continue


                if transaction_id: # Existing transaction, try to update
                    updated_transaction_ids.append(transaction_id)
                    try:
                        t_instance = Transaction.objects.get(id=transaction_id, user=request.user)
                        
                        # Check if anything actually changed to avoid unnecessary updates
                        if (str(t_instance.date) != str(transaction_date) or
                            t_instance.account_id != account_id or
                            t_instance.category_id != category_id or
                            t_instance.description != description or
                            t_instance.amount != amount or
                            t_instance.transaction_type != transaction_type):
                            
                            # Important: Revert old balance impact before applying new
                            if t_instance.account:
                                if t_instance.transaction_type == "income":
                                    t_instance.account.balance -= t_instance.amount
                                else: # expense
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
                else: # New transaction
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

        # Process creations
        created_count = 0
        if transactions_to_create:
            for t_new in transactions_to_create:
                t_new.save()
                created_count += 1
                # Store created transaction data to return
                created_transactions_data.append({
                    'id': t_new.id,
                    'date': t_new.date.strftime('%Y-%m-%d') if hasattr(t_new.date, 'strftime') else str(t_new.date),
                    'amount': float(t_new.amount),
                    'description': t_new.description
                })
            
        

        # Process updates
        updated_count = 0
        accounts_to_recalculate_balance = set()
        if transactions_to_update:
            for t_upd in transactions_to_update:
                t_upd.save() # This will also update account balance via model's save()
                updated_count += 1
                if t_upd.account:
                    accounts_to_recalculate_balance.add(t_upd.account)
            

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
        # Log the exception e
        return JsonResponse({'status': 'error', 'message': f'An unexpected error occurred: {str(e)}'}, status=500)
    

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