from datetime import date, timedelta, datetime
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
        # Validate and convert date
        transaction_date = data.get('date')
        if not transaction_date:
            errors.append("Transaction date is required.")
        else:
            try:
                if isinstance(transaction_date, str):
                    transaction_date = datetime.strptime(transaction_date, "%Y-%m-%d").date() #interpret date as YYYY-MM-DD
                if transaction_date > date.today() + timedelta(days=365 * 10) or transaction_date < date.today() - timedelta(days=365 * 10):
                    errors.append("Transaction date must be within 10 years from today.")
            except ValueError:
                errors.append("Transaction date must be in the format 'YYYY-MM-DD'.")

        # Validate transaction type
        transaction_type = data.get('transaction_type')
        if not transaction_type:
            errors.append("Transaction type is required.")
        elif str(transaction_type).lower() not in ['income', 'expense']:
            errors.append("Transaction type must be either 'income' or 'expense'.")

        # Validate and convert amount
        amount = data.get('amount')
        if not amount:
            errors.append("Transaction amount is required.")
        else:
            try:
                amount = float(amount)
                if amount > 1_000_000 or amount < -1_000_000:
                    errors.append("Amount must be a number between -1,000,000 and 1,000,000.")
            except ValueError:
                errors.append("Amount must be a valid number with at most two decimal places.")

        # Validate description
        description = data.get('description')
        if not description:
            errors.append("Description is required.")
        elif len(description) > 255:
            errors.append("Description cannot be longer than 255 characters.")

        # Raise validation errors if any exist
        if errors:
            raise ValidationError(errors)

    #catch any non-validation errors and log them
    except ValidationError:
        raise
    except Exception as e:
        logger.error(f"Error validating transaction data: {e}", exc_info=True)




