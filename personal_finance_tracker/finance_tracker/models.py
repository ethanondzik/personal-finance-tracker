from django.db import models, transaction
from django.utils import timezone
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.conf import settings
from decimal import Decimal
from django.db.models.signals import post_delete
from django.dispatch import receiver
from django.core.validators import MinValueValidator, MaxValueValidator
import calendar
from datetime import date



class UserManager(BaseUserManager):
     """
    Custom manager for the User model.

    Provides methods to create users with required fields like username, email, and password.
    """
     
     def create_user(self, username, email, name, password=None):
        """
        Creates and returns a new user.

        Args:
            username (str): The username of the user.
            email (str): The email address of the user.
            name (str): The full name of the user.
            password (str, optional): The password for the user.

        Returns:
            User: The created user instance.
        """
        if not email:
            raise ValueError("The Email field must be set")
        if not username:
            raise ValueError("The Username field must be set")
        email = self.normalize_email(email)
        user = self.model(username=username, email=email, name=name)
        user.set_password(password)
        user.save(using=self._db)
        return user


class User(AbstractBaseUser):
    """
    Custom user model for the application.

    Attributes:
        email (EmailField): The user's email address (used for authentication).
        username (CharField): The user's unique username.
        name (CharField): The user's full name.
        is_active (BooleanField): Indicates if the user is active.
        is_staff (BooleanField): Indicates if the user is a staff member (not implemented).
        is_superuser (BooleanField): Indicates if the user is a superuser (not implemented).
        created_at (DateTimeField): The date and time when the user was created.
    """

    email = models.EmailField(unique=True)
    username = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    theme = models.CharField(max_length=20, default="light", choices=[("light", "Light"), ("dark", "Dark")])

    objects = UserManager()

    USERNAME_FIELD = "email"  #use username for authentication

    def __str__(self):
        return self.email


class Account(models.Model):
    """
    Represents a user's bank account.

    Attributes:
        user (ForeignKey): The user who owns the account.
        account_type (CharField): The type of account (e.g., checking, savings).
        balance (DecimalField): The current balance of the account.
        created_at (DateTimeField): The date and time when the account was created.
        account_number (CharField): The unique account number.
        transit_number (CharField): The transit number for the account.
        institution_number (CharField): The institution number for the account.
    """

    ACCOUNT_TYPES = [
        ("checking", "Checking"),
        ("savings", "Savings"),
        ("credit", "Credit"),
        ("investment", "Investment"),
        ("other", "Other"),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    account_type = models.CharField(max_length=50, choices=ACCOUNT_TYPES)
    balance = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    account_number = models.CharField(max_length=10, unique=True)
    transit_number = models.CharField(max_length=10, default="00000")
    institution_number = models.CharField(max_length=10, default="00000")

    def __str__(self):
        return f"Account: {self.account_number}, Balance: {self.balance}, Type: {self.account_type}"


class Category(models.Model):
    """
    Represents a category for transactions.

    Attributes:
        user (ForeignKey): The user who owns the category.
        name (CharField): The name of the category.
        type (CharField): The type of category (income or expense).
    """

    CATEGORY_TYPES = [
        ("income", "Income"),
        ("expense", "Expense"),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    type = models.CharField(max_length=10, choices=CATEGORY_TYPES)

    def __str__(self):
        return self.name


class Transaction(models.Model):
    """
    Represents a financial transaction.

    Attributes:
        user (ForeignKey): The user who owns the transaction.
        account (ForeignKey): The bank account associated with the transaction.
        category (ForeignKey): The category of the transaction.
        amount (DecimalField): The amount of the transaction.
        transaction_type (CharField): The type of transaction (income or expense).
        method (CharField): The method of the transaction (e.g., branch, ATM).
        date (DateField): The date of the transaction.
        description (TextField): A description of the transaction.
    """

    TRANSACTION_TYPES = [
        ("income", "Income"),
        ("expense", "Expense"),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    account = models.ForeignKey(
        Account, on_delete=models.SET_NULL, null=True, blank=True
    )
    category = models.ForeignKey(
        Category, on_delete=models.SET_NULL, null=True, blank=True
    )
    amount = models.DecimalField(max_digits=20, decimal_places=2)
    transaction_type = models.CharField(
        max_length=20,
        choices=[("income", "Income"), ("expense", "Expense")],
        default="expense",
    )

    METHOD_CHOICES = [
        ("branch", "Branch Transaction"),
        ("atm", "Automated Banking Machine"),
        ("telephone", "Telephone Banking Personal"),
    ]
    method = models.CharField(max_length=20, choices=METHOD_CHOICES, null=True, blank=True)
 
    date = models.DateField(default=timezone.now, editable=True)
    description = models.TextField(max_length=255, null=True, blank=True)

    def save(self, *args, **kwargs):
        """
        Extends the default save method.

        - Ensures the amount is a Decimal.
        - Updates the associated account's balance based on the transaction type.
        - Handles both new transactions and updates to existing transactions.

        Args:
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.
        """

        # Ensure amount is a Decimal
        if isinstance(self.amount, str):
            self.amount = Decimal(self.amount)
        # Check if this is a new transaction or an update
        is_new = self.pk is None
        if not is_new:
            # Fetch the original transaction from the database
            original = Transaction.objects.get(pk=self.pk)
            # Revert the original transaction's effect on the account balance
            if original.account:
                if original.transaction_type == "income":
                    original.account.balance -= original.amount
                elif original.transaction_type == "expense":
                    original.account.balance += original.amount
                original.account.save()

        # Apply the new transaction's effect on the account balance
        if self.account:
            with transaction.atomic():
                account = Account.objects.select_for_update().get(pk=self.account.pk)
                if self.transaction_type == "income":
                    account.balance += self.amount
                elif self.transaction_type == "expense":
                    account.balance -= self.amount
                account.save()

        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        """
        Extends the default delete method.

        - Reverts the transaction's effect on the associated account's balance.
        - Deletes the transaction from the database.

        Args:
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.
        """

        # Ensure amount is a Decimal
        if isinstance(self.amount, str):
            self.amount = Decimal(self.amount)
        # Revert the transaction's effect on the account balance before deletion
        if self.account:
            if self.transaction_type == "income":
                self.account.balance -= self.amount
            elif self.transaction_type == "expense":
                self.account.balance += self.amount
            self.account.save()

        super().delete(*args, **kwargs)

    def __str__(self):
        return f"{self.user.email} - {self.transaction_type} - {self.amount}"


@receiver(post_delete, sender=Transaction)
def update_account_balance_on_delete(sender, instance, **kwargs):
    """
    Updates the account balance when a transaction is deleted.

    - If the transaction is of type "income", the transaction amount is subtracted from the account balance.
    - If the transaction is of type "expense", the transaction amount is added back to the account balance.
    - Ensures that the account balance remains accurate after the transaction is removed.

    Args:
        sender (Model): The model class that triggered the signal (Transaction in this case).
        instance (Transaction): The instance of the transaction being deleted.
        **kwargs: Additional keyword arguments.

    Returns:
        None
    """
    if instance.account:
        if isinstance(instance.amount, str):
            instance.amount = Decimal(instance.amount)
        if instance.transaction_type == "income":
            instance.account.balance -= instance.amount
        elif instance.transaction_type == "expense":
            instance.account.balance += instance.amount
        instance.account.save()




class Subscription(models.Model):
    """
    Represents a recurring subscription payment.

    Attributes:
        user (ForeignKey): The user who owns the subscription.
        name (CharField): The name of the subscription (e.g., "Netflix").
        amount (DecimalField): The recurring payment amount.
        account (ForeignKey): The account used for payment.
        category (ForeignKey): The category for this subscription.
        frequency (CharField): How often the payment occurs (monthly, yearly, etc.).
        billing_date (IntegerField): Day of the month when payment is due (1-31).
        start_date (DateField): When the subscription began.
        end_date (DateField): Optional end date for fixed-term subscriptions.
        description (TextField): Additional details about the subscription.
        is_active (BooleanField): Whether the subscription is currently active.
        last_payment_date (DateField): When the last payment was made.
        next_payment_date (DateField): When the next payment is due.
        auto_generate (BooleanField): Whether to auto-generate transaction entries.
    """
    
    FREQUENCY_CHOICES = [
        ("monthly", "Monthly"),
        ("quarterly", "Quarterly"),
        ("semi_annual", "Semi-Annual"),
        ("annual", "Annual"),
        ("weekly", "Weekly"),
        ("biweekly", "Bi-Weekly"),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=20, decimal_places=2)
    account = models.ForeignKey(Account, on_delete=models.SET_NULL, null=True, blank=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES, default="monthly")
    billing_date = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(31)], default=1)
    start_date = models.DateField(default=timezone.now)
    end_date = models.DateField(null=True, blank=True)
    description = models.TextField(max_length=255, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    last_payment_date = models.DateField(null=True, blank=True)
    next_payment_date = models.DateField()
    auto_generate = models.BooleanField(default=False, 
                                        help_text="Automatically generate transaction entries on due dates")
    
    def save(self, *args, **kwargs):
        # Calculate next_payment_date if not explicitly set
        if not self.next_payment_date:
            self.calculate_next_payment_date()
        super().save(*args, **kwargs)
    
    def calculate_next_payment_date(self):
        """Calculate the next payment date based on frequency and billing date"""
        today = timezone.now().date()
        
        # Start with this month's billing date
        current_year = today.year
        current_month = today.month
        
        try:
            next_date = date(current_year, current_month, self.billing_date)
        except ValueError:
            # Handle months with fewer days (e.g., billing_date=31 in February)
            # Use the last day of the month instead
            last_day = calendar.monthrange(current_year, current_month)[1]
            next_date = date(current_year, current_month, last_day)
        
        # If this month's billing date has passed, move to next period
        if next_date < today:
            if self.frequency == "monthly":
                if current_month == 12:
                    next_date = date(current_year + 1, 1, self.billing_date)
                else:
                    try:
                        next_date = date(current_year, current_month + 1, self.billing_date)
                    except ValueError:
                        # Handle months with fewer days
                        next_month = current_month + 1
                        last_day = calendar.monthrange(current_year, next_month)[1]
                        next_date = date(current_year, next_month, min(self.billing_date, last_day))
            elif self.frequency == "annual":
                next_date = date(current_year + 1, current_month, self.billing_date)
        
        self.next_payment_date = next_date
    
    def create_transaction(self):
        """Create a transaction entry for this subscription payment"""
        if not self.is_active:
            return None
            
        transaction = Transaction(
            user=self.user,
            account=self.account,
            category=self.category,
            amount=self.amount,
            transaction_type="expense",
            date=self.next_payment_date,
            description=f"{self.name} subscription payment",
        )
        transaction.save()
        
        # Update subscription payment dates
        self.last_payment_date = self.next_payment_date
        self.calculate_next_payment_date()
        self.save()
        
        return transaction
    
    def __str__(self):
        return f"{self.name} ({self.get_frequency_display()}: ${self.amount})"
    

class Budget(models.Model):
    PERIOD_CHOICES = [
        ('monthly', 'Monthly'),
        ('weekly', 'Weekly'),
        ('yearly', 'Yearly'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    category = models.ForeignKey('Category', on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    period = models.CharField(max_length=10, choices=PERIOD_CHOICES, default='monthly')

    def __str__(self):
        return f"{self.user.username} - {self.category.name} - {self.amount} ({self.period})"


class CustomNotification(models.Model):
    NOTIFICATION_TYPE_CHOICES = [
        ('generic', 'Generic'),
        ('purchase', 'Purchase Size'),
        ('balance', 'Account Balance'),
        ('budget', 'Budget Limit'),
        ('reminder', 'Reminder'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    type = models.CharField(max_length=20, choices=NOTIFICATION_TYPE_CHOICES, default='generic')
    title = models.CharField(max_length=100)
    message = models.TextField(max_length=512)
    threshold = models.FloatField(null=True, blank=True)  # For limits/reminders
    category = models.ForeignKey('Category', null=True, blank=True, on_delete=models.SET_NULL)
    enabled = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    

#implement the following models in the future...
class Debt(models.Model):
    DEBT_TYPES = [
        ("Loan", "Loan"),
        ("Credit Card", "Credit Card"),
        ("Mortgage", "Mortgage"),
    ]
    INTEREST_TYPES = [
        ("Fixed", "Fixed"),
        ("Variable", "Variable"),
    ]
    PAYMENT_FREQUENCIES = [
        ("Monthly", "Monthly"),
        ("Quarterly", "Quarterly"),
        ("Annual", "Annual"),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    account = models.ForeignKey("Account", on_delete=models.SET_NULL, null=True, blank=True)
    debt_type = models.CharField(max_length=50, choices=DEBT_TYPES)
    name = models.CharField(max_length=100)
    principal_amount = models.DecimalField(max_digits=20, decimal_places=2)
    interest_type = models.CharField(max_length=20, choices=INTEREST_TYPES)
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2)
    payment_frequency = models.CharField(max_length=20, choices=PAYMENT_FREQUENCIES)
    remaining_balance = models.DecimalField(max_digits=20, decimal_places=2)
    last_updated = models.DateField(default=timezone.now)

    def __str__(self):
        return f"{self.name} ({self.debt_type})"


class DebtHistory(models.Model):
    UPDATE_SOURCES = [
        ("Bank", "Bank"),
        ("User", "User"),
    ]

    debt = models.ForeignKey(Debt, on_delete=models.CASCADE)
    balance = models.DecimalField(max_digits=20, decimal_places=2)
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2)
    update_source = models.CharField(max_length=50, choices=UPDATE_SOURCES)
    change_date = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"History for {self.debt.name}"


class Payment(models.Model):
    debt = models.ForeignKey(Debt, on_delete=models.CASCADE)
    amount_paid = models.DecimalField(max_digits=20, decimal_places=2)
    payment_date = models.DateField(default=timezone.now)
    remaining_balance = models.DecimalField(max_digits=20, decimal_places=2)

    def __str__(self):
        return f"Payment of {self.amount_paid} for {self.debt.name}"


class Asset(models.Model):
    ASSET_TYPES = [
        ("Stock", "Stock"),
        ("Real Estate", "Real Estate"),
        ("Bond", "Bond"),
        ("Other", "Other"),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    account = models.ForeignKey("Account", on_delete=models.SET_NULL, null=True, blank=True)
    asset_type = models.CharField(max_length=50, choices=ASSET_TYPES)
    name = models.CharField(max_length=100)
    current_value = models.DecimalField(max_digits=20, decimal_places=2)
    last_updated = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.name} ({self.asset_type})"


class StockDetail(models.Model):
    asset = models.OneToOneField(Asset, on_delete=models.CASCADE, primary_key=True)
    ticker = models.CharField(max_length=10, unique=True)
    exchange = models.CharField(max_length=20, null=True, blank=True)
    sector = models.CharField(max_length=50, null=True, blank=True)

    def __str__(self):
        return f"{self.ticker} ({self.exchange})"


class AssetHistory(models.Model):
    UPDATE_SOURCES = [
        ("User", "User"),
        ("API", "API"),
    ]

    asset = models.ForeignKey(Asset, on_delete=models.CASCADE)
    value = models.DecimalField(max_digits=20, decimal_places=2)
    update_source = models.CharField(max_length=50, choices=UPDATE_SOURCES)
    change_date = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"History for {self.asset.name}"