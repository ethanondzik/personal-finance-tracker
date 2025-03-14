from django.shortcuts import render
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required


def landing(request):
    return render(request, 'finance_tracker/landing.html')

@login_required
def dashboard(request):
    return render(request, 'finance_tracker/src/index.html')



