# filepath: /home/ethan/GitHub/personal-finance-tracker/personal_finance_tracker/finance_tracker/views.py
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import Transaction
from .forms import TransactionForm
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login

def landing(request):
    return render(request, 'finance_tracker/landing.html')

@login_required
def dashboard(request):
    transactions = Transaction.objects.filter(user=request.user)
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