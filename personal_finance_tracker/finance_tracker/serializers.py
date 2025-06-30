from rest_framework import serializers
from .models import Transaction, Account, Category, Subscription, Budget, CustomNotification, User

class AccountSerializer(serializers.ModelSerializer):
    user = serializers.ReadOnlyField(source='user.username')

    class Meta:
        model = Account
        fields = ['id', 'user', 'account_number', 'account_type', 'balance']

class CategorySerializer(serializers.ModelSerializer):
    user = serializers.ReadOnlyField(source='user.username')

    class Meta:
        model = Category
        fields = ['id', 'user', 'name', 'type']

class TransactionSerializer(serializers.ModelSerializer):
    user = serializers.ReadOnlyField(source='user.username')
    account = serializers.PrimaryKeyRelatedField(queryset=Account.objects.all())
    category = serializers.PrimaryKeyRelatedField(queryset=Category.objects.all())

    account_details = serializers.StringRelatedField(source='account', read_only=True)
    category_name = serializers.StringRelatedField(source='category', read_only=True)

    class Meta:
        model = Transaction
        fields = [
            'id', 'user', 'date', 'amount', 'transaction_type', 'description',
            'account', 'category', 'account_details', 'category_name'
        ]

    def validate(self, data):
        """
        Check that the account and category belong to the current user.
        """
        request = self.context.get("request")
        if request and hasattr(request, "user"):
            user = request.user
            if 'account' in data and data['account'].user != user:
                raise serializers.ValidationError("The selected account does not belong to you.")
            if 'category' in data and data['category'].user != user:
                raise serializers.ValidationError("The selected category does not belong to you.")
        return data

class SubscriptionSerializer(serializers.ModelSerializer):
    user = serializers.ReadOnlyField(source='user.username')
    account = serializers.PrimaryKeyRelatedField(queryset=Account.objects.all())
    category = serializers.PrimaryKeyRelatedField(queryset=Category.objects.all())

    class Meta:
        model = Subscription
        fields = '__all__'
        read_only_fields = ('user',)

class BudgetSerializer(serializers.ModelSerializer):
    user = serializers.ReadOnlyField(source='user.username')
    category = serializers.PrimaryKeyRelatedField(queryset=Category.objects.all())
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