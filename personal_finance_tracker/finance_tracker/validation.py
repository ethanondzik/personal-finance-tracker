from datetime import date, timedelta
from django.core.exceptions import ValidationError
import re

def validate_transaction_data(data):
    errors = []

    # Validate date
    transaction_date = data.get('date')
    if not transaction_date:
        errors.append("Transaction date is required.")
    elif transaction_date > date.today() + timedelta(days=365 * 10) or transaction_date < date.today() - timedelta(days=365 * 10):
        errors.append("Transaction date must be within 10 years from today.")

    # Validate type
    transaction_type = data.get('type')
    if transaction_type not in ['income', 'expense']:
        errors.append("Transaction type must be either 'income' or 'expense'.")

    # Validate amount
    amount = data.get('amount')
    if not re.match(r'^\d+(\.\d{1,2})?$', str(amount)):
        #REGEX: match 1 or more digit 0-9, optionally followed by a decimal point and 1-2 digits 0-9
        errors.append("Amount must have at most two decimal places.")
    elif amount > 1_000_000 or amount < -1_000_000:
        errors.append("Amount must be a number between -1,000,000 and 1,000,000.")

    # Validate description
    description = data.get('description')
    if not description:
        errors.append("Description is required.")
    elif len(description) > 255:
        errors.append("Description cannot be longer than 255 characters.")

    # Validate category
    category = data.get('category')
    if category not in ['food', 'rent', 'utilities', 'entertainment', 'other']:
        errors.append("Category must be one of: 'food', 'rent', 'utilities', 'entertainment', 'other'.")
    # Validate category for income transactions
    if transaction_type == 'income' and category != 'other':
        errors.append("Income transactions must have the category 'other'.")


    # Validate is_recurring
    is_recurring = data.get('is_recurring')
    if is_recurring not in ['True', 'False', True, False, 'true', 'false', 1, 0]:
        errors.append("Is_recurring must be either True or False (case-insensitive).")
    else:
        # Convert to boolean for further processing
        is_recurring = str(is_recurring).lower() in ['true', '1']

    # Validate recurrence_interval
    recurrence_interval = data.get('recurrence_interval')
    if is_recurring and recurrence_interval not in ['daily', 'weekly', 'monthly', 'yearly']:
        errors.append("Recurring transactions must have a recurrence interval of 'daily', 'weekly', 'monthly', or 'yearly'.")
    elif not is_recurring and recurrence_interval:
        errors.append("Non-recurring transactions cannot have a recurrence interval.")

    # Validate payment_method
    payment_method = data.get('payment_method')
    if payment_method not in ['cash', 'credit_card', 'bank_transfer', 'other']:
        errors.append("Payment method must be one of: 'cash', 'credit_card', 'bank_transfer', 'other'.")

    # Validate status
    status = data.get('status')
    if status not in ['pending', 'completed', 'canceled']:
        errors.append("Status must be one of: 'pending', 'completed', 'canceled'.")

    # Validate notes
    notes = data.get('notes', '')
    if len(notes) > 512:
        errors.append("Notes cannot be longer than 512 characters.")

    # Validate currency
    currency = data.get('currency', '')
    if len(currency) > 20:
        errors.append("Currency cannot be longer than 20 characters.")
    elif currency not in ['CAD', 'USD', 'EUR', 'GBP', 'AUD']:  #need to find list or reference to all valid currency codes
        errors.append("Currency must be a recognized currency like 'CAD', 'USD', 'EUR', etc.")

    # Validate location
    location = data.get('location', '')
    if location and len(location) > 255:
        errors.append("Location cannot be longer than 255 characters.")

    # Validate tags
    tags = data.get('tags', '')
    if len(tags) > 255:
        errors.append("Tags cannot be longer than 255 characters.")

    
    if errors:
        raise ValidationError(errors)