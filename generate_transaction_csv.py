import csv
import random
from datetime import datetime, timedelta

# Define the output file path
output_file = "generated_transactions.csv"

# Define the default categories and accounts
categories = [
    {"name": "Salary", "type": "income"},
    {"name": "Groceries", "type": "expense"},
    {"name": "Transport", "type": "expense"},
    {"name": "Freelance", "type": "income"},
    {"name": "Utilities", "type": "expense"},
]

#adjust accounts to match the sample user as required
accounts = [
    {"account_number": "44564376", "account_type": "checking"},
    {"account_number": "44569771", "account_type": "savings"},
]

# Define the range for transaction amounts
amount_ranges = {
    "income": (100, 5000),  # Income transactions will have amounts between 100 and 5000
    "expense": (10, 1000),  # Expense transactions will have amounts between 10 and 1000
}

# Generate a random date within the last 2 years
def random_date():
    start_date = datetime.now() - timedelta(days=730)
    end_date = datetime.now()
    return start_date + (end_date - start_date) * random.random()

# Generate 100 valid transactions
transactions = []
for _ in range(100):
    category = random.choice(categories)
    account = random.choice(accounts)
    transaction_type = category["type"]
    amount = round(random.uniform(*amount_ranges[transaction_type]), 2)
    date = random_date().strftime("%Y-%m-%d")
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
    writer = csv.DictWriter(file, fieldnames=["date", "transaction_type", "amount", "description", "category", "account"])
    writer.writeheader()
    writer.writerows(transactions)

print(f"Generated {len(transactions)} transactions in '{output_file}'.")