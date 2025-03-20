from django import forms
from .models import Transaction
from datetime import date, timedelta

class TransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = [
            'date', 'type', 'amount', 'description', 'category',
            'is_recurring', 'recurrence_interval', 'payment_method',
            'status', 'notes', 'currency', 'location', 'tags'
        ]
    
    # Apply bootstrap form control class to all form fields so they look nice
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if field_name != 'is_recurring':
                field.widget.attrs['class'] = 'form-control'

        # Add placeholders for input fields
        self.fields['date'].widget.attrs['placeholder'] = 'YYYY-MM-DD'
        self.fields['type'].widget.attrs['placeholder'] = 'Select transaction type (e.g., income, expense)'
        self.fields['amount'].widget.attrs['placeholder'] = 'Enter the transaction amount (e.g., 100.00)'
        self.fields['description'].widget.attrs['placeholder'] = 'Enter a brief description (e.g., Grocery shopping)'
        self.fields['category'].widget.attrs['placeholder'] = 'Select a category (e.g., Food, Rent, Other)'
        self.fields['is_recurring'].widget.attrs['placeholder'] = 'Check if this is a recurring transaction'
        self.fields['recurrence_interval'].widget.attrs['placeholder'] = 'Enter recurrence interval (e.g., Monthly)'
        self.fields['payment_method'].widget.attrs['placeholder'] = 'Select payment method (e.g., Credit Card, Cash)'
        self.fields['status'].widget.attrs['placeholder'] = 'Select transaction status (e.g., Completed, Pending)'
        self.fields['notes'].widget.attrs['placeholder'] = 'Add any additional notes (optional)'
        self.fields['currency'].widget.attrs['placeholder'] = 'Enter currency (e.g., USD, EUR)'
        self.fields['location'].widget.attrs['placeholder'] = 'Enter location (e.g., New York, Online)'
        self.fields['tags'].widget.attrs['placeholder'] = 'Enter tags separated by commas (e.g., groceries, food)'


    # Field-specific validation for `amount`
    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        upper_bound = 1000000
        lower_bound = -1000000
        if amount > upper_bound or amount < lower_bound:
            raise forms.ValidationError(f"Amount must a number between {lower_bound} and {upper_bound}.")
        return amount

    # Field-specific validation for `date`
    def clean_date(self):
        transaction_date = self.cleaned_data.get('date')
        upper_bound = date.today() + timedelta(days=365*10)
        lower_bound = date.today() - timedelta(days=365*10)
        if transaction_date > upper_bound or transaction_date < lower_bound:
            raise forms.ValidationError("Transaction date cannot be in the future.")
        return transaction_date

    # Cross-field validation
    def clean(self):
        cleaned_data = super().clean()
        transaction_type = cleaned_data.get('type')
        category = cleaned_data.get('category')

        # Ensure income transactions have the category 'other'
        if transaction_type == 'income' and category != 'other':
            raise forms.ValidationError("Income transactions must have the category 'other'.")

        # Ensure recurring transactions have a recurrence interval
        is_recurring = cleaned_data.get('is_recurring')
        recurrence_interval = cleaned_data.get('recurrence_interval')
        if is_recurring and not recurrence_interval:
            raise forms.ValidationError("Recurring transactions must have a recurrence interval.")

        return cleaned_data

class CSVUploadForm(forms.Form):
    file = forms.FileField(label="Upload CSV File")