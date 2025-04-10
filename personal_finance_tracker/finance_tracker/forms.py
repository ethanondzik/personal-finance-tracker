from django import forms
from .models import Transaction, Account, Category, User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

import csv
import mimetypes

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
    - Validates that the account number is unique for the user.

    Attributes:
        account_type (CharField): The type of the bank account (e.g., checking, savings).
        balance (DecimalField): The initial balance of the account.
        account_number (CharField): The unique account number.
        transit_number (CharField): The transit number for the account.
        institution_number (CharField): The institution number for the account.

    Methods:
        clean(): Validates the form data.
    """
    class Meta:
        model = Account
        fields = [
            #"user",
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
    - Validates that the category name and type are unique for the user.

    Attributes:
        name (CharField): The name of the category.
        type (CharField): The type of the category (e.g., income or expense).

    Methods:
        clean(): Validates the form data.
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

    - Validates the uploaded file type, size, and contents.
    - Processes each row in the CSV file and validates the data.

    Attributes:
        file (FileField): The uploaded CSV file.
        validated_rows (list): A list of validated rows from the CSV file.

    Methods:
        clean_file(): Validates the uploaded file and processes its contents.
    """
    file = forms.FileField(label="Upload CSV File")

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)  # Pass the user to the form
        super().__init__(*args, **kwargs)
        self.validated_rows = []  # Store validated rows here

    def clean_file(self):
        file = self.cleaned_data.get("file")

        # Validate file type
        if not file.name.endswith(".csv"):
            raise forms.ValidationError("Only CSV files are allowed.")

        # Check MIME type - ensure it is a valid csv
        mime_type, _ = mimetypes.guess_type(file.name)
        if mime_type != "text/csv":
            raise forms.ValidationError("The uploaded file is not a valid CSV file.")

        # Validate file size
        max_file_size = 10 * 1024 * 1024  # 5 MB
        if file.size > max_file_size:
            raise forms.ValidationError("The uploaded file is too large. Maximum size allowed is 5 MB.")

        # Validate File Contents Row by Row
        try:
            decoded_file = file.read().decode("utf-8").splitlines()
            reader = csv.DictReader(decoded_file)
            errors = []

            for row_number, row in enumerate(reader, start=1):
                # Resolve and Validate category
                category_value = row.get("category")
                if category_value:
                    try:
                        row["category"] = Category.objects.get(name=category_value, user=self.user)
                    except Category.DoesNotExist:
                        errors.append(f"Row {row_number}: Invalid category '{category_value}'.")

                # Resolve and Validate account
                account_value = row.get("account")
                if account_value:
                    try:
                        row["account"] = Account.objects.get(account_number=account_value, user=self.user)
                    except Account.DoesNotExist:
                        errors.append(f"Row {row_number}: Invalid account '{account_value}'.")

                try:
                    validate_transaction_data(row)
                except ValidationError as e:
                    errors.append(f"Row {row_number}: {', '.join(e.messages)}")

                #store row data 
                self.validated_rows.append(row)

        except Exception as e:
            errors.append(f"Error processing file: {e}")

        if errors:
            raise forms.ValidationError(errors)

        return file
    

class TransactionQueryForm(forms.Form):
    """
    A form for querying transactions based on various filters.

    Attributes:
        keyword (CharField): A keyword to search in transaction descriptions or categories.
        date_range (ChoiceField): A predefined date range for filtering transactions.
        start_date (DateField): The start date for a custom date range.
        end_date (DateField): The end date for a custom date range.
        min_amount (DecimalField): The minimum transaction amount.
        max_amount (DecimalField): The maximum transaction amount.
        transaction_type (ChoiceField): The type of transaction (e.g., income, expense).
        transaction_method (ChoiceField): The method of the transaction (e.g., branch, ATM).
    """

    keyword = forms.CharField(
        required=False, 
        label="Keyword Search", 
        widget=forms.TextInput(attrs={"placeholder": "Search by description or category"})
    )
    date_range = forms.ChoiceField(
        required=False,
        label="Date Range",
        choices=[
            ("4weeks", "Last 4 Weeks"),
            ("3m", "Last 3 Months"),
            ("6m", "Last 6 Months"),
            ("12m", "Last 12 Months"),
            ("custom", "Custom Range"),
        ],
        widget=forms.Select(attrs={"class": "form-select"})
    )
    start_date = forms.DateField(
        required=False, 
        label="Start Date", 
        widget=forms.DateInput(attrs={"type": "date", "id": "id_start_date"})
    )
    end_date = forms.DateField(
        required=False, 
        label="End Date", 
        widget=forms.DateInput(attrs={"type": "date", "id": "id_end_date"})
    )
    min_amount = forms.DecimalField(
        required=False, 
        label="Min Amount", 
        widget=forms.NumberInput(attrs={"placeholder": "Minimum Amount"})
    )
    max_amount = forms.DecimalField(
        required=False, 
        label="Max Amount", 
        widget=forms.NumberInput(attrs={"placeholder": "Maximum Amount"})
    )
    transaction_type = forms.ChoiceField(
        required=False,
        label="Transaction Type",
        choices=[
            ("all", "All"),
            ("all_debits", "All Debits"),
            ("all_credits", "All Credits"),
            ("cheques", "Cheques"),
            ("debit_memos", "Debit Memos"),
            ("recurring_payments", "Recurring Payments"),
            ("pre_authorized_payments", "Pre-Authorized Payments"),
            ("credit_memos", "Credit Memos"),
            ("fees", "Fees"),
            ("purchases", "Purchases"),
            ("cash_advance", "Cash Advance and Balance Transfer"),
            ("payments", "Payments"),
            ("interest", "Interest"),
        ],
        widget=forms.Select(attrs={"class": "form-select"}),
        initial = "all"
    )
    transaction_method = forms.ChoiceField(
        required=False,
        label="Transaction Method",
        choices=[
            ("all", "All"),
            ("branch", "Branch Transaction"),
            ("atm", "Automated Banking Machine"),
            ("telephone", "Telephone Banking Personal"),
        ],
        widget=forms.Select(attrs={"class": "form-select"}),
        initial = "all"
    )


class AccountManagementForm(forms.ModelForm):
    """
    A form for managing user account details.

    - Allows users to update their username, email, and name.
    - Validates that the username and email are unique.

    Attributes:
        username (CharField): The user's username.
        email (EmailField): The user's email address.
        name (CharField): The user's full name.

    Methods:
        clean_email(): Validates that the email is unique.
        clean_username(): Validates that the username is unique.
    """
    
    class Meta:
        model = User
        fields = ["username", "email", "name"]

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if User.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("This email is already in use.")
        return email

    def clean_username(self):
        username = self.cleaned_data.get("username")
        if User.objects.filter(username=username).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("This username is already in use.")
        return username