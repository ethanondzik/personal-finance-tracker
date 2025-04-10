from django.db import models, transaction
from django.utils import timezone
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.conf import settings
from decimal import Decimal
from django.db.models.signals import post_delete
from django.dispatch import receiver



class UserManager(BaseUserManager):
     def create_user(self, username, email, name, password=None):
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
    email = models.EmailField(unique=True)
    username = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = UserManager()

    USERNAME_FIELD = "email"  #use username for authentication

    def __str__(self):
        return self.email



class Account(models.Model):
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


# Signal to handle account balance update after a transaction is deleted
@receiver(post_delete, sender=Transaction)
def update_account_balance_on_delete(sender, instance, **kwargs):
    if instance.account:
        if isinstance(instance.amount, str):
            instance.amount = Decimal(instance.amount)
        if instance.transaction_type == "income":
            instance.account.balance -= instance.amount
        elif instance.transaction_type == "expense":
            instance.account.balance += instance.amount
        instance.account.save()


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