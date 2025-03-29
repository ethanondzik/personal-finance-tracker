# filepath: /home/ethan/GitHub/personal-finance-tracker/personal_finance_tracker/finance_tracker/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Transaction, Account, Category
from .forms import TransactionForm, CSVUploadForm, BankAccountForm, CategoryForm
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.http import HttpResponseNotAllowed
from django.contrib import messages
from .validation import validate_transaction_data
from django.core.exceptions import ValidationError
from datetime import date
import csv
import json
from collections import defaultdict

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
    }

    return render(request, 'finance_tracker/dashboard.html', {
        'transactions': transactions,
        'chart_data': chart_data,   
        #'accounts': accounts,
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
        form = TransactionForm(request.POST)
        if form.is_valid():
            transaction = form.save(commit=False)
            transaction.user = request.user
            transaction.save()
            messages.success(request, "Transaction added successfully!")
            return redirect('dashboard')
        else:
            messages.error(request, "Error adding transaction. Please try again.")
    else:
        form = TransactionForm()
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
            user = form.save()
            login(request, user)
            return redirect('dashboard')
        else:
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
    if request.method == 'POST':
        form = CSVUploadForm(request.POST, request.FILES)
        if form.is_valid():
            csv_file = request.FILES['file']
            try:
                decoded_file = csv_file.read().decode('utf-8').splitlines()
                reader = csv.DictReader(decoded_file)
                errors = []
                for row_number, row in enumerate(reader, start=1):
                    # Convert CSV row values to the correct types
                    try:
                        row_data = {
                            'date': date.fromisoformat(row['date']),
                            'type': row['type'],
                            'amount': float(row['amount']),
                            'description': row['description'],
                            'category': row['category'],
                            'is_recurring': row['is_recurring'].lower() == 'true',
                            'recurrence_interval': row.get('recurrence_interval', None),
                            'payment_method': row['payment_method'],
                            'status': row['status'],
                            'notes': row.get('notes', ''),
                            'currency': row.get('currency', 'CAD'),
                            'location': row.get('location', ''),
                            'tags': row.get('tags', '')
                        }
                        # Validate the row
                        validate_transaction_data(row_data)

                        # Create the transaction if valid
                        Transaction.objects.create(
                            user=request.user,
                            **row_data
                        )
                    except ValidationError as e:
                        errors.append(f"Row {row_number}: {', '.join(e.messages)}")
                    except Exception as e:
                        errors.append(f"Row {row_number}: {str(e)}")

                if errors:
                    for error in errors:
                        messages.error(request, error)
                else:
                    messages.success(request, "Transactions uploaded successfully!")
                return redirect('dashboard')
            except Exception as e:
                messages.error(request, f"Error processing file: {e}")
    else:
        form = CSVUploadForm()
    return render(request, 'finance_tracker/upload_transactions.html', {'form': form})



@login_required
def add_category(request):
    """
    Handles the addition of a new category for the logged-in user.
    - If the request method is POST, validates the submitted form data and saves the category.
    - If the request method is GET, displays an empty form for the user to fill out.
    Args:
        request (HttpRequest): The HTTP request object.
    Returns:
        HttpResponse: The rendered add category page with the form.
        HttpResponseRedirect: Redirects to the dashboard if the category is successfully added.
    """
    # Placeholder function for adding a category
    # Implement the logic to add a category here
    return render(request, 'finance_tracker/add_category.html')



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