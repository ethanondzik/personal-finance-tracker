# filepath: /home/ethan/GitHub/personal-finance-tracker/personal_finance_tracker/finance_tracker/urls.py
from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', views.landing, name='landing'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='landing'), name='logout'),
    path('register/', views.register, name='register'),
    path('add_transaction/', views.add_transaction, name='add_transaction'),
    path('update_transaction/<int:transaction_id>/', views.update_transaction, name='update_transaction'),
    #path('delete_transaction/<int:transaction_id>/', views.delete_transaction, name='delete_transaction'),
    path('delete-transactions/', views.delete_transactions, name='delete_transactions'),
    path('upload_transactions/', views.upload_transactions, name='upload_transactions'),
    path('password_reset/', auth_views.PasswordResetView.as_view(), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),
]