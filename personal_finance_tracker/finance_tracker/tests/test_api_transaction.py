import pytest
from rest_framework.test import APIClient
from rest_framework import status
from finance_tracker.test_generator import UserFactory, AccountFactory, CategoryFactory, TransactionFactory
from finance_tracker.models import Transaction

# Mark all tests in this file as needing database access
pytestmark = pytest.mark.django_db

@pytest.fixture
def api_client():
    """Fixture for API client."""
    return APIClient()

@pytest.fixture
def user():
    """Fixture for a regular user."""
    return UserFactory()

@pytest.fixture
def another_user():
    """Fixture for another user to test permissions."""
    return UserFactory()

def test_transaction_list_unauthenticated(api_client):
    """
    GIVEN: An unauthenticated user
    WHEN: They try to access the transaction list endpoint
    THEN: They should receive a 403 FORBIDDEN error.
    """
    response = api_client.get('/api/transactions/')
    assert response.status_code == status.HTTP_403_FORBIDDEN

def test_transaction_list_authenticated(api_client, user, another_user):
    """
    GIVEN: An authenticated user with transactions
    WHEN: They access the transaction list endpoint
    THEN: They should receive a 200 OK response with only their transactions.
    """
    # Create transactions for the main user and another user
    TransactionFactory.create_batch(5, user=user)
    TransactionFactory.create_batch(3, user=another_user)

    api_client.force_authenticate(user=user)
    response = api_client.get('/api/transactions/')

    assert response.status_code == status.HTTP_200_OK
    # The API should only return the 5 transactions belonging to the authenticated user
    assert response.data['count'] == 5
    assert len(response.data['results']) == 5

def test_create_transaction(api_client, user):
    """
    GIVEN: An authenticated user
    WHEN: They send a POST request to create a transaction
    THEN: A new transaction should be created and associated with them.
    """
    account = AccountFactory(user=user)
    category = CategoryFactory(user=user, type='expense')
    
    transaction_data = {
        'account': account.id,
        'category': category.id,
        'date': '2025-07-01',
        'amount': '99.99',
        'description': 'Test Purchase',
        'transaction_type': 'expense'
    }

    api_client.force_authenticate(user=user)
    response = api_client.post('/api/transactions/', data=transaction_data, format='json')

    assert response.status_code == status.HTTP_201_CREATED
    assert Transaction.objects.count() == 1
    new_transaction = Transaction.objects.first()
    assert new_transaction.user == user
    assert new_transaction.description == 'Test Purchase'

def test_cannot_use_another_users_account(api_client, user, another_user):
    """
    GIVEN: An authenticated user
    WHEN: They try to create a transaction using another user's account
    THEN: They should receive a 400 Bad Request error.
    """
    other_users_account = AccountFactory(user=another_user)
    category = CategoryFactory(user=user, type='expense')

    transaction_data = {
        'account': other_users_account.id,
        'category': category.id,
        'date': '2025-07-01',
        'amount': '50.00',
        'description': 'Malicious attempt',
        'transaction_type': 'expense'
    }

    api_client.force_authenticate(user=user)
    response = api_client.post('/api/transactions/', data=transaction_data, format='json')

    # Your UserScopedPrimaryKeyRelatedField should raise a validation error
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert 'account' in response.data
    assert Transaction.objects.count() == 0

def test_transaction_filtering_by_type(api_client, user):
    """
    GIVEN: An authenticated user with income and expense transactions
    WHEN: They filter the transaction list by 'income'
    THEN: They should only receive income transactions.
    """
    TransactionFactory.create_batch(3, user=user, category__type='income', transaction_type='income')
    TransactionFactory.create_batch(4, user=user, category__type='expense', transaction_type='expense')

    api_client.force_authenticate(user=user)
    response = api_client.get('/api/transactions/?transaction_type=income')

    assert response.status_code == status.HTTP_200_OK
    assert response.data['count'] == 3
    for transaction in response.data['results']:
        assert transaction['transaction_type'] == 'income'

def test_transaction_search(api_client, user):
    """
    GIVEN: An authenticated user with several transactions
    WHEN: They use the search parameter
    THEN: They should receive only transactions matching the search term.
    """
    TransactionFactory(user=user, description='Weekly grocery shopping')
    TransactionFactory(user=user, description='Monthly rent payment')
    TransactionFactory(user=user, description='Coffee shop grocery run')

    api_client.force_authenticate(user=user)
    response = api_client.get('/api/transactions/?search=grocery')

    assert response.status_code == status.HTTP_200_OK
    assert response.data['count'] == 2

def test_transaction_ordering(api_client, user):
    """
    GIVEN: An authenticated user with transactions
    WHEN: They use the ordering parameter
    THEN: The results should be ordered correctly.
    """
    TransactionFactory(user=user, amount=100)
    TransactionFactory(user=user, amount=50)
    TransactionFactory(user=user, amount=200)

    api_client.force_authenticate(user=user)
    response = api_client.get('/api/transactions/?ordering=amount') # Ascending

    assert response.status_code == status.HTTP_200_OK
    amounts = [t['amount'] for t in response.data['results']]
    assert amounts == ['50.00', '100.00', '200.00']

    response_desc = api_client.get('/api/transactions/?ordering=-amount') # Descending
    amounts_desc = [t['amount'] for t in response_desc.data['results']]
    assert amounts_desc == ['200.00', '100.00', '50.00']

def test_transaction_summary_action(api_client, user):
    """
    GIVEN: An authenticated user with transactions
    WHEN: They access the /summary custom action
    THEN: They should receive correct summary statistics.
    """
    TransactionFactory(user=user, transaction_type='income', amount=1000)
    TransactionFactory(user=user, transaction_type='income', amount=500)
    TransactionFactory(user=user, transaction_type='expense', amount=100)
    TransactionFactory(user=user, transaction_type='expense', amount=50)

    api_client.force_authenticate(user=user)
    response = api_client.get('/api/transactions/summary/')

    assert response.status_code == status.HTTP_200_OK
    data = response.data
    assert data['total_transactions'] == 4
    assert data['total_income'] == 1500
    assert data['total_expenses'] == 150
    assert data['net_amount'] == 1350