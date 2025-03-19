from django import forms
from .models import Transaction

class TransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = [
            'date', 'type', 'amount', 'description', 'category',
            'is_recurring', 'recurrence_interval', 'payment_method',
            'status', 'notes', 'currency', 'location', 'tags'
        ]

class CSVUploadForm(forms.Form):
    file = forms.FileField(label="Upload CSV File")