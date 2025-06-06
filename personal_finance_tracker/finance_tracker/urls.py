from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', views.landing, name='landing'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='landing'), name='logout'),
    path('register/', views.register, name='register'),
    path("manage_account/", views.manage_account, name="manage_account"),
    path('add_transaction/', views.add_transaction, name='add_transaction'),
    path('update_transaction/<int:transaction_id>/', views.update_transaction, name='update_transaction'),
    path('delete-transactions/', views.delete_transactions, name='delete_transactions'),
    path('upload_transactions/', views.upload_transactions, name='upload_transactions'),
    path('manage_bank_accounts/', views.manage_bank_accounts, name='manage_bank_accounts'),
    path('manage_categories/', views.manage_categories, name='manage_categories'),
    path("query-transactions/", views.query_transactions, name="query_transactions"),
    path('password_reset/', auth_views.PasswordResetView.as_view(), name='password_reset'),
    path('manage-subscriptions/', views.manage_subscriptions, name='manage_subscriptions'),
    path('update-subscription/<int:subscription_id>/', views.update_subscription, name='update_subscription'),
    path('update-theme-preference/', views.update_theme_preference, name='update_theme_preference'),
    path('transactions/calendar/', views.transaction_calendar, name='transaction_calendar'),
    path('transactions/timeline/', views.transaction_timeline, name='transaction_timeline'),
    path('notifications/', views.notification_settings, name='notification_settings'),
    path('delete-custom-notification/<int:notification_id>/', views.delete_custom_notification, name='delete_custom_notification'),
    path('manage-budgets/', views.manage_budgets, name='manage_budgets'),
    path('transactions/spreadsheet/', views.spreadsheet_transactions, name='spreadsheet_transactions'),
    path('transactions/spreadsheet/save/', views.save_spreadsheet_transactions, name='save_spreadsheet_transactions'),

]