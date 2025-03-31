from django import forms
from .models import Transaction, Account, Category, User
from datetime import date, timedelta
from django.core.exceptions import ValidationError

from .validation import validate_transaction_data




class UserCreationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ["email", "username", "name", "password"]

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password != confirm_password:
            raise forms.ValidationError("Passwords do not match.")

        return cleaned_data




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

    def clean(self):
        cleaned_data = super().clean()
        transaction_data = {
            "date": cleaned_data.get("date"),
            "transaction_type": cleaned_data.get("transaction_type"),
            "amount": cleaned_data.get("amount"),
            "description": cleaned_data.get("description"),
            "category": cleaned_data.get("category"),
        }
        try:
            validate_transaction_data(transaction_data)
        except ValidationError as e:
            for error in e:
                print(error)
                self.add_error(None, error)
        return cleaned_data



class BankAccountForm(forms.ModelForm):
    class Meta:
        model = Account
        fields = [
            "user",
            "account_type", 
            "balance",
            # "created_at",
            "account_number",
            "transit_number",
            "institution_number",
        ]
        
    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)
        

    def clean(self):
        cleaned_data = super().clean()
        return cleaned_data

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ["name", "type"]
        labels = {
            "name": "Category Name",
            "type": "Category Type",
        }
        
    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)
        


class CSVUploadForm(forms.Form):
    file = forms.FileField(label="Upload CSV File")