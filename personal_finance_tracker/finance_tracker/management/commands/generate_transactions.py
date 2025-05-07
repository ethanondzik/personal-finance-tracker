import os
import csv
import random
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Generates a CSV file with random transaction data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=100,
            help='Number of transactions to generate'
        )
        parser.add_argument(
            '--output',
            type=str,
            default='generated_transactions.csv',
            help='Output file path relative to test_data directory'
        )

    def handle(self, *args, **options):
        # Determine file path
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(
                        os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
        output_dir = os.path.join(project_root, 'test_data')
        os.makedirs(output_dir, exist_ok=True)
        
        output_file = os.path.join(output_dir, options['output'])
        
        # Define the default categories and accounts
        categories = [
            {"name": "Salary", "type": "income"},
            {"name": "Groceries", "type": "expense"},
            {"name": "Transport", "type": "expense"},
            {"name": "Freelance", "type": "income"},
            {"name": "Utilities", "type": "expense"},
        ]

        # Adjust accounts to match the sample user
        accounts = [
            {"account_number": "44564376", "account_type": "checking"},
            {"account_number": "44569771", "account_type": "savings"},
        ]

        # Define the range for transaction amounts
        amount_ranges = {
            "income": (100, 5000),  # Income transactions between 100 and 5000
            "expense": (10, 1000),  # Expense transactions between 10 and 1000
        }

        # Generate transactions
        transactions = []
        for _ in range(options['count']):
            category = random.choice(categories)
            account = random.choice(accounts)
            transaction_type = category["type"]
            amount = round(random.uniform(*amount_ranges[transaction_type]), 2)
            date = self.random_date().strftime("%Y-%m-%d")
            description = f"{category['name']} transaction"
            transactions.append({
                "date": date,
                "transaction_type": transaction_type,
                "amount": amount,
                "description": description,
                "category": category["name"],
                "account": account["account_number"],
            })

        # Write the transactions to a CSV file
        with open(output_file, mode="w", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=[
                "date", "transaction_type", "amount", 
                "description", "category", "account"])
            writer.writeheader()
            writer.writerows(transactions)

        self.stdout.write(
            self.style.SUCCESS(f"Generated {len(transactions)} transactions in '{output_file}'.")
        )

    def random_date(self):
        """Generate a random date within the last 2 years, change as desired"""
        start_date = datetime.now() - timedelta(days=730)
        end_date = datetime.now()
        return start_date + (end_date - start_date) * random.random()