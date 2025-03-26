# filepath: /home/ethan/GitHub/personal-finance-tracker/personal_finance_tracker/finance_tracker/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Transaction
from .forms import TransactionForm, CSVUploadForm
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.http import HttpResponseNotAllowed
from django.contrib import messages
from .validation import validate_transaction_data
from django.core.exceptions import ValidationError
from datetime import date
import csv

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
    Displays the dashboard with a list of all transactions for the logged-in user.

    Args:
        request (HttpRequest): The HTTP request object.

    Returns:
        HttpResponse: The rendered dashboard page with the user's transactions.
    """
    transactions = Transaction.objects.filter(user=request.user)
    #print(transactions)
    #return render(request, 'finance_tracker/dashboard.html', {'transactions': transactions})
    # Prepare chart data
    dates = []
    income = []
    expenses = []
    
    # Aggregate data by date and type
    chart_data = {}
    for t in transactions:
        key = t.date.isoformat()
        if key not in chart_data:
            chart_data[key] = {'income': 0, 'expense': 0}
        if t.type == 'income':
            chart_data[key]['income'] += float(t.amount)
        else:
            chart_data[key]['expense'] += float(t.amount)
    
    # Sort dates and populate arrays
    sorted_dates = sorted(chart_data.keys())
    for date in sorted_dates:
        dates.append(date)
        income.append(chart_data[date]['income'])
        expenses.append(chart_data[date]['expense'])
    
    return render(request, 'finance_tracker/dashboard.html', {
        'transactions': transactions,
        'chart_data': {
            'dates': dates,
            'income': income,
            'expenses': expenses
        }
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