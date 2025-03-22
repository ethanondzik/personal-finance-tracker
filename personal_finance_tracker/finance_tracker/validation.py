from datetime import date, timedelta
from django.core.exceptions import ValidationError

def validate_transaction_data(data):
    errors = []

    # Validate date
    transaction_date = data.get('date')
    if transaction_date > date.today() + timedelta(days=365*10) or transaction_date < date.today() - timedelta(days=365*10):
        errors.append("Transaction date must be within 10 years from today.")

    # Validate amount
    amount = data.get('amount')
    if amount > 1_000_000 or amount < -1_000_000:
        errors.append("Amount must be a number between -1,000,000 and 1,000,000.")

    # Validate category for income transactions
    transaction_type = data.get('type')
    category = data.get('category')
    if transaction_type == 'income' and category != 'other':
        errors.append("Income transactions must have the category 'other'.")

    # Validate recurrence interval for recurring transactions
    is_recurring = data.get('is_recurring')
    recurrence_interval = data.get('recurrence_interval')
    if is_recurring and not recurrence_interval:
        errors.append("Recurring transactions must have a recurrence interval.")

    if errors:
        raise ValidationError(errors)