from django import forms
from .models import Transaction
from datetime import date, timedelta

from .validation import validate_transaction_data

class TransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = [
            'date', 'type', 'amount', 'description', 'category',
            'is_recurring', 'recurrence_interval', 'payment_method',
            'status', 'notes', 'currency', 'location', 'tags'
        ]

    def clean(self):
        cleaned_data = super().clean()
        try:
            validate_transaction_data(cleaned_data)
        except forms.ValidationError as e:
            raise forms.ValidationError(e.messages)
        return cleaned_data
    
class CSVUploadForm(forms.Form):
    file = forms.FileField(label="Upload CSV File")