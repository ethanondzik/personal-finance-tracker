import django_filters
from datetime import date, timedelta
from django.db.models import Q
from .models import Transaction, Account, Category, Subscription, Budget, CustomNotification

class TransactionFilter(django_filters.FilterSet):
    # Date filtering
    start_date = django_filters.DateFilter(field_name='date', lookup_expr='gte', help_text="Filter transactions from this date")
    end_date = django_filters.DateFilter(field_name='date', lookup_expr='lte', help_text="Filter transactions until this date")
    
    # Predefined date ranges
    date_range = django_filters.ChoiceFilter(
        choices=[
            ('today', 'Today'),
            ('yesterday', 'Yesterday'),
            ('this_week', 'This Week'),
            ('last_week', 'Last Week'),
            ('this_month', 'This Month'),
            ('last_month', 'Last Month'),
            ('this_quarter', 'This Quarter'),
            ('this_year', 'This Year'),
            ('last_7_days', 'Last 7 Days'),
            ('last_30_days', 'Last 30 Days'),
            ('last_90_days', 'Last 90 Days'),
            ('last_year', 'Last Year'),
        ],
        method='filter_date_range',
        help_text="Select a predefined date range",
        label='Date Range'
    )
    
    # Amount filtering
    min_amount = django_filters.NumberFilter(field_name='amount', lookup_expr='gte', help_text="Minimum amount")
    max_amount = django_filters.NumberFilter(field_name='amount', lookup_expr='lte', help_text="Maximum amount")
    amount_range = django_filters.RangeFilter(field_name='amount', help_text="Amount range (e.g., 100,500)")
    
    # Text search across multiple fields
    search = django_filters.CharFilter(method='filter_search', help_text="Search in description, category name, or account number", label='Search')
    
    # Category filtering (will be user-scoped in __init__)
    category = django_filters.ModelChoiceFilter(queryset=Category.objects.none(), help_text="Filter by category")
    category_type = django_filters.ChoiceFilter(
        field_name='category__type',
        choices=Category.CATEGORY_TYPES,
        help_text="Filter by category type"
    )
    
    # Account filtering (will be user-scoped in __init__)
    account = django_filters.ModelChoiceFilter(queryset=Account.objects.none(), help_text="Filter by account")
    account_type = django_filters.ChoiceFilter(
        field_name='account__account_type',
        choices=Account.ACCOUNT_TYPES,
        help_text="Filter by account type"
    )
    
    # Transaction type
    transaction_type = django_filters.ChoiceFilter(
        field_name='transaction_type',
        choices=Transaction.TRANSACTION_TYPES,
        help_text="Filter by transaction type"
    )
    
    # Method filtering
    method = django_filters.ChoiceFilter(
        field_name='method',
        choices=Transaction.METHOD_CHOICES,
        help_text="Filter by transaction method"
    )
    
    # Date field lookups
    date_year = django_filters.NumberFilter(field_name='date__year', help_text="Filter by year", label='Year')
    date_month = django_filters.NumberFilter(field_name='date__month', help_text="Filter by month (1-12)", label='Month (1-12)')
    date_day = django_filters.NumberFilter(field_name='date__day', help_text="Filter by day of month", label='Day of Month')
    
    # Has category or account
    has_category = django_filters.BooleanFilter(method='filter_has_category', help_text="Filter transactions with/without category", label='Has Category')
    has_account = django_filters.BooleanFilter(method='filter_has_account', help_text="Filter transactions with/without account", label='Has Account')

    class Meta:
        model = Transaction
        fields = {
            'amount': ['exact', 'gte', 'lte', 'gt', 'lt'],
            'date': ['exact', 'gte', 'lte', 'year', 'month', 'day'],
            'transaction_type': ['exact'],
            'method': ['exact'],
            'description': ['icontains', 'iexact'],
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # User-scope the queryset filters
        if self.request and hasattr(self.request, 'user'):
            user = self.request.user
            self.filters['category'].queryset = Category.objects.filter(user=user)
            self.filters['account'].queryset = Account.objects.filter(user=user)

    def filter_date_range(self, queryset, name, value):
        """Filter by predefined date ranges"""
        today = date.today()
        
        if value == 'today':
            return queryset.filter(date=today)
        elif value == 'yesterday':
            yesterday = today - timedelta(days=1)
            return queryset.filter(date=yesterday)
        elif value == 'this_week':
            start = today - timedelta(days=today.weekday())
            return queryset.filter(date__gte=start)
        elif value == 'last_week':
            start = today - timedelta(days=today.weekday() + 7)
            end = start + timedelta(days=6)
            return queryset.filter(date__range=[start, end])
        elif value == 'this_month':
            start = today.replace(day=1)
            return queryset.filter(date__gte=start)
        elif value == 'last_month':
            first_day_this_month = today.replace(day=1)
            last_day_last_month = first_day_this_month - timedelta(days=1)
            first_day_last_month = last_day_last_month.replace(day=1)
            return queryset.filter(date__range=[first_day_last_month, last_day_last_month])
        elif value == 'this_quarter':
            quarter = (today.month - 1) // 3 + 1
            start = date(today.year, (quarter - 1) * 3 + 1, 1)
            return queryset.filter(date__gte=start)
        elif value == 'this_year':
            start = date(today.year, 1, 1)
            return queryset.filter(date__gte=start)
        elif value == 'last_7_days':
            start = today - timedelta(days=7)
            return queryset.filter(date__gte=start)
        elif value == 'last_30_days':
            start = today - timedelta(days=30)
            return queryset.filter(date__gte=start)
        elif value == 'last_90_days':
            start = today - timedelta(days=90)
            return queryset.filter(date__gte=start)
        elif value == 'last_year':
            start = date(today.year - 1, 1, 1)
            end = date(today.year - 1, 12, 31)
            return queryset.filter(date__range=[start, end])
        
        return queryset

    def filter_search(self, queryset, name, value):
        """Search across description, category name, and account number"""
        return queryset.filter(
            Q(description__icontains=value) |
            Q(category__name__icontains=value) |
            Q(account__account_number__icontains=value)
        )

    def filter_has_category(self, queryset, name, value):
        """Filter transactions with or without category"""
        if value:
            return queryset.filter(category__isnull=False)
        else:
            return queryset.filter(category__isnull=True)

    def filter_has_account(self, queryset, name, value):
        """Filter transactions with or without account"""
        if value:
            return queryset.filter(account__isnull=False)
        else:
            return queryset.filter(account__isnull=True)
        

class AccountFilter(django_filters.FilterSet):
    balance_gte = django_filters.NumberFilter(field_name='balance', lookup_expr='gte', label='Balance Greater Than or Equal To')
    balance_lte = django_filters.NumberFilter(field_name='balance', lookup_expr='lte', label='Balance Less Than or Equal To')
    
    class Meta:
        model = Account
        exclude = ['user']


class CategoryFilter(django_filters.FilterSet):
    class Meta:
        model = Category
        exclude = ['user']


class SubscriptionFilter(django_filters.FilterSet):
    min_amount = django_filters.NumberFilter(field_name='amount', lookup_expr='gte')
    max_amount = django_filters.NumberFilter(field_name='amount', lookup_expr='lte')
    next_payment_date_after = django_filters.DateFilter(field_name='next_payment_date', lookup_expr='gte')
    next_payment_date_before = django_filters.DateFilter(field_name='next_payment_date', lookup_expr='lte')

    class Meta:
        model = Subscription
        exclude = ['user']


class BudgetFilter(django_filters.FilterSet):
    min_amount = django_filters.NumberFilter(field_name='amount', lookup_expr='gte')
    max_amount = django_filters.NumberFilter(field_name='amount', lookup_expr='lte')
    
    class Meta:
        model = Budget
        exclude = ['user']


class CustomNotificationFilter(django_filters.FilterSet):
    notification_date_after = django_filters.DateTimeFilter(field_name='notification_datetime', lookup_expr='gte')
    notification_date_before = django_filters.DateTimeFilter(field_name='notification_datetime', lookup_expr='lte')

    class Meta:
        model = CustomNotification
        exclude = ['user']