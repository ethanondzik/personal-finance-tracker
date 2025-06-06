import os
import sys
import django

# Set up project paths
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PARENT_DIR = os.path.join(PROJECT_ROOT, "personal_finance_tracker")
sys.path.append(PARENT_DIR)

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'personal_finance_tracker.settings')
django.setup()

# Import after Django setup
from finance_tracker.models import Account, Category, User

def populate_sample_data():
    # Create a sample user
    username = "test_user"
    email = "test.user@example.com"
    name = "Test User"
    password = "Test1234$"

    if not User.objects.filter(username=username).exists():
        user = User.objects.create_user(username=username, email=email, name=name, password=password)
        print(f"Created user: {username}")
    else:
        user = User.objects.get(username=username)
        print(f"User {username} already exists.")

    # Define sample categories
    categories = [
        {"name": "Salary", "type": "income"},
        {"name": "Groceries", "type": "expense"},
        {"name": "Transport", "type": "expense"},
        {"name": "Freelance", "type": "income"},
        {"name": "Utilities", "type": "expense"},
        {"name": "Rent", "type": "expense"},
        {"name": "Entertainment", "type": "expense"},
        {"name": "Investments", "type": "income"},
        {"name": "Miscellaneous", "type": "expense"},
        {"name": "Insurance", "type": "expense"},
        {"name": "Travel", "type": "expense"},
        {"name": "Gifts", "type": "expense"},
        {"name": "Subscriptions", "type": "expense"},
    ]

    # Add categories to the database
    for category_data in categories:
        category, created = Category.objects.get_or_create(
            user=user,
            name=category_data["name"],
            type=category_data["type"]
        )
        if created:
            print(f"Added category: {category.name}")
        else:
            print(f"Category {category.name} already exists.")

    # Define sample accounts
    accounts = [
        {"account_number": "44564376", "account_type": "checking", "balance": 1000.00},
        {"account_number": "44569771", "account_type": "savings", "balance": 5000.00},
    ]

    # Add accounts to the database
    for account_data in accounts:
        account, created = Account.objects.get_or_create(
            user=user,
            account_number=account_data["account_number"],
            defaults={
                "account_type": account_data["account_type"],
                "balance": account_data["balance"],
            }
        )
        if created:
            print(f"Added account: {account.account_number}")
        else:
            print(f"Account {account.account_number} already exists.")

    print("Sample data population complete.")


if __name__ == "__main__":
    populate_sample_data()