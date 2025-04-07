# filepath: /home/ethan/GitHub/personal-finance-tracker/personal_finance_tracker/finance_tracker/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Transaction, Account, Category
from .forms import TransactionForm, CSVUploadForm, BankAccountForm, CategoryForm, UserCreationForm, TransactionQueryForm
from django.contrib.auth import login
from django.contrib import messages
from .validation import validate_transaction_data
from django.core.exceptions import ValidationError
from datetime import date, timedelta
import csv
from collections import defaultdict
from django.db import models
from django.db.models import Sum, Q
from django.db.models.functions import TruncMonth


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
    #accounts = Account.objects.filter(user=request.user)
    accounts = Account.objects.filter(user=request.user).values(
        'account_number', 'account_type', 'balance'
    )
    
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

    return render(request, 'finance_tracker/dashboard.html', {
        'transactions': transactions,
        'chart_data': chart_data,   
        'accounts': accounts,
    })

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
    if request.method == 'POST':
        form = TransactionForm(request.POST, user=request.user)
        if form.is_valid():
            transaction = form.save(commit=False)
            transaction.user = request.user
            transaction.save()
            messages.success(request, "Transaction added successfully!")
            return redirect('dashboard')
        else:
            messages.error(request, "Error adding transaction. Please try again.")
    else:
        form = TransactionForm(user=request.user)
    return render(request, 'finance_tracker/add_transaction.html', {'form': form})
    

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
            print(f"User {user.username} registered successfully.")
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

    if request.method == 'POST':
        form = TransactionForm(request.POST, instance=transaction)
        if form.is_valid():
            form.save()
            return redirect('dashboard')
        else:
            messages.error(request, "Error updating transaction. Please try again.")
    else:
        form = TransactionForm(instance=transaction)

    return render(request, 'finance_tracker/update_transaction.html', {'form': form, 'transaction': transaction})




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
        transaction_ids = request.POST.getlist('transaction_ids')
        if 'confirm' in request.POST: #confirm is hidden submission in the delete_transactions form
            # User has confirmed deletion
            transactions = Transaction.objects.filter(id__in=transaction_ids, user=request.user)
            count = transactions.count()
            
            if count > 0:
                transactions.delete()
                messages.success(request, f"{count} transaction(s) deleted successfully!")
            else:
                messages.error(request, "No valid transactions found to delete.")
        
    return redirect('dashboard')




@login_required
def upload_transactions(request):
    """
    Handles the upload of transactions via a CSV file for the logged-in user.

    - If the request method is POST, processes the uploaded CSV file, validates each row, and saves valid transactions.
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
        form = BankAccountForm(request.POST)
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
        

    return render(request, "finance_tracker/query_transactions.html", {
        "form": form,
        "transactions": transactions,
    })