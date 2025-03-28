from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Account(models.Model):
    ACCOUNT_TYPES = [
        ("checking", "Checking"),
        ("savings", "Savings"),
        ("credit", "Credit"),
        ("investment", "Investment"),
        ("other", "Other"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    account_type = models.CharField(max_length=50, choices=ACCOUNT_TYPES)
    balance = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    account_number = models.CharField(max_length=10, unique=True)
    transit_number = models.CharField(max_length=10, unique=True)
    institution_number = models.CharField(max_length=10, default=00000)

    def __str__(self):
        return f"Account: {self.account_number}, Balance: {self.balance}, Type: {self.account_type}"


class Category(models.Model):
    CATEGORY_TYPES = [
        ("income", "Income"),
        ("expense", "Expense"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    type = models.CharField(max_length=10, choices=CATEGORY_TYPES)

    def __str__(self):
        return self.name


class Transaction(models.Model):
    TRANSACTION_TYPES = [
        ("income", "Income"),
        ("expense", "Expense"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    account = models.ForeignKey(
        Account, on_delete=models.SET_NULL, null=True, blank=True
    )
    category = models.ForeignKey(
        Category, on_delete=models.SET_NULL, null=True, blank=True
    )
    amount = models.DecimalField(max_digits=20, decimal_places=2)
    transaction_type = models.CharField(
        max_length=20,
        choices=[("income", "Income"), ("expense", "Expense")],
        default="expense",
    )
 
    date = models.DateField(default=timezone.now, editable=True)
    description = models.TextField(max_length=255, null=True, blank=True)

    def __str__(self):
        return f"{self.user.username} - {self.transaction_type} - {self.amount}"

