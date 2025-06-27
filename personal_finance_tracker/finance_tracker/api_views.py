from rest_framework import viewsets, permissions
from .models import Transaction, Account, Category, Subscription, Budget, CustomNotification
from .serializers import (
    TransactionSerializer, AccountSerializer, CategorySerializer,
    SubscriptionSerializer, BudgetSerializer, CustomNotificationSerializer
)

class IsOwner(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to view or edit it.
    """
    def has_object_permission(self, request, view, obj):
        return obj.user == request.user

class UserScopedViewSet(viewsets.ModelViewSet):
    """
    A base ViewSet that automatically filters querysets by the current user
    and sets the user on creation.
    """
    permission_classes = [permissions.IsAuthenticated, IsOwner]

    def get_queryset(self):
        """
        This view should return a list of all the objects
        for the currently authenticated user.
        """
        return self.queryset.filter(user=self.request.user)

    def perform_create(self, serializer):
        """
        Set the user of the object to the current user.
        """
        serializer.save(user=self.request.user)



# --- ViewSets for each model ---

class TransactionViewSet(UserScopedViewSet):
    queryset = Transaction.objects.all().select_related('account', 'category')
    serializer_class = TransactionSerializer

class AccountViewSet(UserScopedViewSet):
    queryset = Account.objects.all()
    serializer_class = AccountSerializer

class CategoryViewSet(UserScopedViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer

class SubscriptionViewSet(UserScopedViewSet):
    queryset = Subscription.objects.all()
    serializer_class = SubscriptionSerializer

class BudgetViewSet(UserScopedViewSet):
    queryset = Budget.objects.all().select_related('category')
    serializer_class = BudgetSerializer

class CustomNotificationViewSet(UserScopedViewSet):
    queryset = CustomNotification.objects.all()
    serializer_class = CustomNotificationSerializer