from django import forms
from .models import Transaction, Account, Category, User
from datetime import date, timedelta
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

from .validation import validate_transaction_data




class UserCreationForm(forms.ModelForm):
    """
    A form for creating new users.

    - Includes fields for email, username, name, password, and confirm_password.
    - Validates that the password and confirm_password match.
    - Enforces password strength using Django's built-in password validation.

    Attributes:
        password (CharField): A field for entering the user's password.
        confirm_password (CharField): A field for confirming the user's password.

    Methods:
        clean(): Validates the form data, ensuring passwords match and meet strength requirements.
    """
    password = forms.CharField(widget=forms.PasswordInput, label="Password")
    confirm_password = forms.CharField(widget=forms.PasswordInput, label="Confirm Password")


    class Meta:
        model = User #custom user model
        fields = ["username", "email", "name", "password"]

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password != confirm_password:
            raise forms.ValidationError("Passwords do not match.")
        
        # Validate password strength
        try:
            validate_password(password)
        except ValidationError as e:
            self.add_error("password", e.messages)
        print("Password validation complete")
        return cleaned_data




class TransactionForm(forms.ModelForm):
    """
    A form for creating or updating transactions.

    - Filters the account and category fields to include only those belonging to the logged-in user.
    - Validates transaction data using a custom validation function.

    Attributes:
        account (ForeignKey): The account associated with the transaction.
        category (ForeignKey): The category associated with the transaction.

    Methods:
        __init__(user): Filters the account and category fields based on the logged-in user.
        clean(): Validates the transaction data using the validate_transaction_data function.
    """
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
                self.add_error(None, error)
        return cleaned_data



class BankAccountForm(forms.ModelForm):
    """
    A form for creating or updating bank accounts.

    - Filters the user field to include only the logged-in user.

    Attributes:
        user (ForeignKey): The user associated with the bank account.

    Methods:
        __init__(user): Filters the user field based on the logged-in user.
        clean(): Validates the form data.
    """
    class Meta:
        model = Account
        fields = [
            "user",
            "account_type", 
            "balance",
            "account_number",
            "transit_number",
            "institution_number",
        ]
        
    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)
        

    def clean(self):
        cleaned_data = super().clean()
        account_number = cleaned_data.get('account_number')
        user = self.instance.user if self.instance and self.instance.user else self.initial.get('user')

        if Account.objects.filter(account_number=account_number, user=user).exists():
            raise forms.ValidationError(f"A bank account with the number {account_number} already exists.")
        return cleaned_data

class CategoryForm(forms.ModelForm):
    """
    A form for creating or updating categories.

    - Filters the user field to include only the logged-in user.

    Attributes:
        name (CharField): The name of the category.
        type (CharField): The type of the category (e.g., income or expense).

    Methods:
        __init__(user): Filters the user field based on the logged-in user.
    """
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

    def clean(self):
        cleaned_data = super().clean()
        name = cleaned_data.get('name')
        category_type = cleaned_data.get('type')
        user = self.instance.user if self.instance and self.instance.user else self.initial.get('user')

        if Category.objects.filter(name=name, type=category_type, user=user).exists():
            raise forms.ValidationError(f"A category with the name '{name}' and type '{category_type}' already exists.")
        return cleaned_data
        


class CSVUploadForm(forms.Form):
    """
    A form for uploading CSV files.

    Attributes:
        file (FileField): The uploaded CSV file.
    """
    file = forms.FileField(label="Upload CSV File")