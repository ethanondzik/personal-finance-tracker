from django.db import models
from django.contrib.auth.models import User

class Transaction(models.Model):
    TRANSACTION_TYPES = [
        ('income', 'Income'),
        ('expense', 'Expense'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField()
    type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    amount = models.DecimalField(max_digits=20, decimal_places=2)
    description = models.TextField()
    category = models.CharField(max_length=50, choices=[
        ('food', 'Food'),
        ('rent', 'Rent'),
        ('utilities', 'Utilities'),
        ('entertainment', 'Entertainment'),
        ('other', 'Other'),
    ],
        default='other'
    )
    is_recurring = models.BooleanField(default=False)
    recurrence_interval = models.CharField(max_length=20, choices=[
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('yearly', 'Yearly'),
    ], null=True, blank=True)
    payment_method = models.CharField(max_length=20, choices=[
        ('cash', 'Cash'),
        ('credit_card', 'Credit Card'),
        ('bank_transfer', 'Bank Transfer'),
        ('other', 'Other'),
    ],
        default='other'
    )
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('canceled', 'Canceled'),
    ], 
        default='completed'
    )
    notes = models.TextField(null=True, blank=True)
    currency = models.CharField(max_length=20, default='CAD')
    linked_transaction = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True)
    location = models.CharField(max_length=255, null=True, blank=True)
    tags = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return f"[{self.id}] - {self.user.username} - {self.type} - {self.amount}"