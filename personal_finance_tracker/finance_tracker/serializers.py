from rest_framework import serializers
from .models import Transaction, Account, Category, Subscription, Budget, CustomNotification, User


class UserScopedPrimaryKeyRelatedField(serializers.PrimaryKeyRelatedField):
    """Custom field that automatically filters queryset by current user"""
    
    def get_queryset(self):
        request = self.context.get('request', None)
        queryset = super().get_queryset()
        if not request or not queryset:
            return queryset
        return queryset.filter(user=request.user)   


class AccountSerializer(serializers.ModelSerializer):

    class Meta:
        model = Account
        fields = ['id', 'user', 'account_number', 'account_type', 'balance', 'created_at', 'transit_number', 'institution_number']
        read_only_fields = ('user',)


class CategorySerializer(serializers.ModelSerializer):

    class Meta:
        model = Category
        fields = ['id', 'user', 'name', 'type']
        read_only_fields = ('user',)

class TransactionSerializer(serializers.ModelSerializer):
    account = UserScopedPrimaryKeyRelatedField(queryset=Account.objects.all())
    category = UserScopedPrimaryKeyRelatedField(
        queryset=Category.objects.all(), 
        allow_null=True, 
        required=False
    )

    account_details = serializers.StringRelatedField(source='account', read_only=True)
    category_name = serializers.StringRelatedField(source='category', read_only=True)
    account_number = serializers.CharField(source='account.account_number', read_only=True)
    account_type = serializers.CharField(source='account.account_type', read_only=True)
    account_balance = serializers.DecimalField(source='account.balance', max_digits=20, decimal_places=2, read_only=True)
    category_type = serializers.CharField(source='category.type', read_only=True)

    # Computed fields
    formatted_amount = serializers.SerializerMethodField()
    age_days = serializers.SerializerMethodField()

    class Meta:
        model = Transaction
        fields = [
            'id', 'date', 'amount', 'transaction_type', 'description',
            'account', 'category', 'method', 'created_at', 'updated_at',
            # Related field details
            'account_details', 'category_name', 'account_number', 
            'account_type', 'account_balance', 'category_type',
            # Computed fields
            'formatted_amount', 'age_days'
        ]
        read_only_fields = ('user', 'created_at', 'updated_at')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Support field selection via query parameter
        fields = self.context.get('request', {}).query_params.get('fields')
        if fields:
            fields = fields.split(',')
            allowed = set(fields)
            existing = set(self.fields)
            for field_name in existing - allowed:
                self.fields.pop(field_name)

        

    def get_formatted_amount(self, obj):
        """Return formatted amount with currency"""
        return f"${obj.amount:,.2f}"

    def get_age_days(self, obj):
        """Return how many days ago this transaction occurred"""
        from datetime import date
        return (date.today() - obj.date).days

class SubscriptionSerializer(serializers.ModelSerializer):
    user = serializers.ReadOnlyField(source='user.username')
    account = UserScopedPrimaryKeyRelatedField(
        queryset=Account.objects.all(), 
        allow_null=True, 
        required=False
    )
    category = UserScopedPrimaryKeyRelatedField(
        queryset=Category.objects.filter(type='expense'),  # Only expense categories for subscriptions
        allow_null=True, 
        required=False
    )

    class Meta:
        model = Subscription
        fields = '__all__'
        read_only_fields = ('user',)

class BudgetSerializer(serializers.ModelSerializer):
    category = UserScopedPrimaryKeyRelatedField(queryset=Category.objects.all())
    category_name = serializers.StringRelatedField(source='category', read_only=True)

    class Meta:
        model = Budget
        fields = ['id', 'user', 'category', 'category_name', 'amount', 'period']

class CustomNotificationSerializer(serializers.ModelSerializer):
    user = serializers.ReadOnlyField(source='user.username')

    class Meta:
        model = CustomNotification
        fields = '__all__'
        read_only_fields = ('user',)