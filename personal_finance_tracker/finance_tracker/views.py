# filepath: /home/ethan/GitHub/personal-finance-tracker/personal_finance_tracker/finance_tracker/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Transaction
from .forms import TransactionForm, CSVUploadForm
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.http import HttpResponseNotAllowed
from django.contrib import messages
import csv

def landing(request):
    return render(request, 'finance_tracker/landing.html')

@login_required
def dashboard(request):
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
    if request.method == 'POST':
        form = TransactionForm(request.POST)
        if form.is_valid():
            transaction = form.save(commit=False)
            transaction.user = request.user
            transaction.save()
            return redirect('dashboard')
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
def delete_transaction(request, transaction_id):
    transaction = get_object_or_404(Transaction, id=transaction_id, user=request.user)
    if request.method == 'POST':
        transaction.delete()
        return redirect('dashboard')
    else:
        return render(request, 'finance_tracker/delete_transaction.html', {'transaction': transaction})
    


@login_required
def upload_transactions(request):
    if request.method == 'POST':
        form = CSVUploadForm(request.POST, request.FILES)
        if form.is_valid():
            csv_file = request.FILES['file']
            try:
                decoded_file = csv_file.read().decode('utf-8').splitlines()
                reader = csv.DictReader(decoded_file)
                for row in reader:
                    Transaction.objects.create(
                        user=request.user,
                        date=row['date'],
                        type=row['type'],
                        amount=row['amount'],
                        description=row['description'],
                        category=row.get('category', 'other'),
                        is_recurring=row.get('is_recurring', 'False') == 'True',
                        recurrence_interval=row.get('recurrence_interval', None),
                        payment_method=row.get('payment_method', 'other'),
                        status=row.get('status', 'completed'),
                        notes=row.get('notes', ''),
                        currency=row.get('currency', 'CAD'),
                        location=row.get('location', ''),
                        tags=row.get('tags', '')
                    )
                messages.success(request, "Transactions uploaded successfully!")
                return redirect('dashboard')
            except Exception as e:
                messages.error(request, f"Error processing file: {e}")
    else:
        form = CSVUploadForm()
    return render(request, 'finance_tracker/upload_transactions.html', {'form': form})