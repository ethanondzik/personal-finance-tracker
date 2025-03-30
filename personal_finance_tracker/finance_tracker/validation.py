from datetime import date, timedelta
from django.core.exceptions import ValidationError
import re
import logging

logger = logging.getLogger(__name__) #create logger specific to this module


"""
This module contains validation logic for transaction data in the personal finance tracker application.
The `validate_transaction_data` function ensures that all transaction fields meet the required constraints
and business rules before being processed or saved to the database.
"""
def validate_transaction_data(data):
    """
    Validates the transaction data dictionary to ensure all fields meet the required constraints.

    Args:
        data (dict): A dictionary containing transaction data to validate. Expected keys include:
            - date (datetime.date): The transaction date.
            - type (str): The transaction type ('income' or 'expense').
            - amount (float or str): The transaction amount.
            - description (str): A brief description of the transaction.

    Raises:
        ValidationError: If any field fails validation, a list of error messages is raised.

    Returns:
        None: If validation passes, the function completes without raising an exception.
    """

    errors = []

    try:
        # Validate date
        transaction_date = data.get('date')
        if not transaction_date:
            errors.append("Transaction date is required.")
        elif transaction_date > date.today() + timedelta(days=365 * 10) or transaction_date < date.today() - timedelta(days=365 * 10):
            errors.append("Transaction date must be within 10 years from today.")

        # Validate type
        transaction_type = data.get('type')
        if transaction_type and str(transaction_type).lower() not in ['income', 'expense']:
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


        if errors:
            raise ValidationError(errors)
    except Exception as e:
        logger.error(f"Error validating transaction data: {e}", exc_info=True)
        raise e