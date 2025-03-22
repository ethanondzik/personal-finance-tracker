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
    return render(request, 'finance_tracker/landing.html')


@login_required
def dashboard(request):
    transactions = Transaction.objects.filter(user=request.user)
    print(transactions)
    return render(request, 'finance_tracker/dashboard.html', {'transactions': transactions})

@login_required
def add_transaction(request):
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
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('dashboard')
        else:
            print(form.errors)  # Print form errors to the console for debugging
    else:
        form = UserCreationForm()
    return render(request, 'finance_tracker/register.html', {'form': form})


@login_required
def update_transaction(request, transaction_id):
    transaction = get_object_or_404(Transaction, id=transaction_id, user=request.user)

    if request.method == 'POST':
        form = TransactionForm(request.POST, instance=transaction)
        if form.is_valid():
            form.save()
            return redirect('dashboard')
        else:
            print(form.errors)  # Debugging: Print form errors if invalid
    elif request.method == 'GET':
        form = TransactionForm(instance=transaction)
    else:
        # Reject any non-GET or non-POST requests
        return HttpResponseNotAllowed(['GET', 'POST'])

    return render(request, 'finance_tracker/update_transaction.html', {'form': form, 'transaction': transaction})




@login_required
def delete_transactions(request):
    if request.method == 'POST':
        transaction_ids = request.POST.getlist('transaction_ids')
        print(request.POST)
        if 'confirm' in request.POST:
            # User has confirmed deletion
            transactions = Transaction.objects.filter(id__in=transaction_ids, user=request.user)
            count = transactions.count()
            
            if count > 0:
                transactions.delete()
                messages.success(request, f"{count} transaction(s) deleted successfully!")
            else:
                messages.error(request, "No valid transactions found to delete.")
        
        return redirect('dashboard')
    else:
        return redirect('dashboard')




@login_required
def upload_transactions(request):
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