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

    class Meta:
        model = Transaction
        fields = [
            'id', 'user', 'date', 'amount', 'transaction_type', 'description',
            'account', 'category', 'account_details', 'category_name', 'method', 
        ]
        read_only_fields = ('user',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Get the current user from the request context
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            user = request.user
            # Filter querysets to only show current user's data
            self.fields['account'].queryset = Account.objects.filter(user=user)
            self.fields['category'].queryset = Category.objects.filter(user=user)
        else:
            # Fallback: empty querysets if no user context
            self.fields['account'].queryset = Account.objects.none()
            self.fields['category'].queryset = Category.objects.none()


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