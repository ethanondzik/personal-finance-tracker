import factory
from factory.django import DjangoModelFactory
from .models import User, Account, Category, Transaction, Subscription, Budget, CustomNotification
from django.utils import timezone


class UserFactory(DjangoModelFactory):
    class Meta:
        model = User
        django_get_or_create = ('username',)
        skip_postgeneration_save = True

    username = factory.Faker('user_name')
    email = factory.Faker('email')
    @factory.post_generation
    def password(obj, create, extracted, **kwargs):
        """
        Set and save the user's password after the user object is created.
        Usage: UserFactory(password='some-strong-password')
        """
        if not create:
            # Simple build, do nothing
            return
        
        # Use the provided password, or a default if none was provided
        password_to_set = extracted if extracted else 'defaultpassword'
        obj.set_password(password_to_set)
        # Explicitly save the object again to persist the hashed password
        obj.save()

class AccountFactory(DjangoModelFactory):
    class Meta:
        model = Account

    user = factory.SubFactory(UserFactory)
    account_number = factory.Faker('pystr', max_chars=10)
    account_type = factory.Iterator(['checking', 'savings'])
    balance = factory.Faker('pydecimal', left_digits=5, right_digits=2, positive=True)

class CategoryFactory(DjangoModelFactory):
    class Meta:
        model = Category

    user = factory.SubFactory(UserFactory)
    name = factory.Faker('word')
    type = factory.Iterator(['income', 'expense'])

class TransactionFactory(DjangoModelFactory):
    class Meta:
        model = Transaction

    user = factory.SubFactory(UserFactory)
    account = factory.SubFactory(AccountFactory, user=factory.SelfAttribute('..user'))
    category = factory.SubFactory(CategoryFactory, user=factory.SelfAttribute('..user'))
    date = factory.Faker('date_between', start_date='-1y', end_date='today')
    amount = factory.Faker('pydecimal', left_digits=3, right_digits=2, positive=True)
    description = factory.Faker('sentence')
    transaction_type = factory.SelfAttribute('category.type')

class SubscriptionFactory(DjangoModelFactory):
    class Meta:
        model = Subscription

    user = factory.SubFactory(UserFactory)
    name = factory.Faker('word')
    amount = factory.Faker('pydecimal', left_digits=3, right_digits=2, positive=True)
    frequency = factory.Iterator(['monthly', 'yearly'])
    start_date = factory.Faker('date_this_year')
    end_date = factory.Faker('date_between', start_date='today', end_date='+1y')

class BudgetFactory(DjangoModelFactory):
    class Meta:
        model = Budget

    user = factory.SubFactory(UserFactory)
    category = factory.SubFactory(CategoryFactory, user=factory.SelfAttribute('..user'))
    amount = factory.Faker('pydecimal', left_digits=3, right_digits=2, positive=True)
    start_date = factory.Faker('date_this_year')
    end_date = factory.Faker('date_between', start_date='today', end_date='+1y')

class CustomNotificationFactory(DjangoModelFactory):
    class Meta:
        model = CustomNotification

    user = factory.SubFactory(UserFactory)
    message = factory.Faker('sentence')
    notification_type = factory.Iterator(['email', 'sms', 'push'])
    created_at = factory.LazyFunction(timezone.now)
    is_active = True


