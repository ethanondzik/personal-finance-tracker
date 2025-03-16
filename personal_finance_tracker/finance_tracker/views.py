from django.shortcuts import render, redirect
from django.contrib.auth import views as auth_views
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm


def landing(request):
    return render(request, 'finance_tracker/landing.html')

@login_required
def dashboard(request):
    return render(request, 'finance_tracker/dashboard.html')

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('dashboard')
        else:
            print(form.errors)
    else:
        form = UserCreationForm()
    return render(request, 'finance_tracker/register.html', {'form': form})




