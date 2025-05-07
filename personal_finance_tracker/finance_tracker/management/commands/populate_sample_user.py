from django.core.management.base import BaseCommand
from finance_tracker.models import Account, Category, User
from django.conf import settings
from django.db import IntegrityError

class Command(BaseCommand):
    help = 'Populates the database with a sample user, categories, and bank accounts'

    def handle(self, *args, **kwargs):
        self.stdout.write("Creating sample user data...")
        self.populate_sample_data()
        self.stdout.write(self.style.SUCCESS("Sample data population complete."))

    def populate_sample_data(self):
        # Create a sample user
        username = "test_user"
        email = "testuser@example.com"
        name = "Test User"
        password = "Test1234$"

        if not User.objects.filter(username=username).exists():
            user = User.objects.create_user(username=username, email=email, name=name, password=password)
            self.stdout.write(f"Created user: {username}")
        else:
            user = User.objects.get(username=username)
            self.stdout.write(f"User {username} already exists.")

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
                self.stdout.write(f"Added category: {category.name}")
            else:
                self.stdout.write(f"Category {category.name} already exists.")

        # Define sample accounts
        accounts = [
            {"account_number": "44564376", "account_type": "checking", "balance": 1000.00},
            {"account_number": "44569771", "account_type": "savings", "balance": 5000.00},
        ]

        # Add accounts to the database
        for account_data in accounts:
            try:
                account, created = Account.objects.get_or_create(
                    user=user,
                    account_number=account_data["account_number"],
                    defaults={
                        "account_type": account_data["account_type"],
                        "balance": account_data["balance"],
                    }
                )
        
                if created:
                    self.stdout.write(f"Added account: {account.account_number}")
                else:
                    self.stdout.write(f"Account {account.account_number} already exists.")
            except IntegrityError as e:
                existing_account = Account.objects.filter(account_number=account_data["account_number"]).first()
                if existing_account:
                    self.stdout.write(f"Account {existing_account.account_number} already exists.")
                else:
                    self.stdout.write(f"Account {account_data['account_number']} conflicts with existing data.")
                
            except Exception as e:
                raise e #If any other error occues that is not an Integrity Error, raise it