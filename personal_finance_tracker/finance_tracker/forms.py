from django import forms
from .models import Transaction, Account, Category
from datetime import date, timedelta

from .validation import validate_transaction_data

class TransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = [
            "account",
            "category",
            "amount",
            "transaction_type",
            "date",
            "description",
        ]

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        if user:
            self.fields["account"].queryset = Account.objects.filter(user=user)
            self.fields["category"].queryset = Category.objects.filter(user=user)
    
class CSVUploadForm(forms.Form):
    file = forms.FileField(label="Upload CSV File")