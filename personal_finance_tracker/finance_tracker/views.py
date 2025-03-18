# filepath: /home/ethan/GitHub/personal-finance-tracker/personal_finance_tracker/finance_tracker/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Transaction
from .forms import TransactionForm
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.http import HttpResponseNotAllowed

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