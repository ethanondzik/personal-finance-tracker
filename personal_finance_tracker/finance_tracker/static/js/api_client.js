/**
 * A dedicated API client for interacting with the Django REST Framework backend. Essentially an abstraction in the hopes
 *  of making JS more organized and easier to read.
 */
(function(window) {
    'use strict';

    function getCSRFToken() {
        const cookieValue = document.cookie
            .split('; ')
            .find(row => row.startsWith('csrftoken='))
            ?.split('=')[1];
        return cookieValue || '';
    }

    async function _request(endpoint, method = 'GET', body = null) {
        const options = {
            method: method,
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken(),
                'Accept': 'application/json',
            }
        };

        if (body) {
            options.body = JSON.stringify(body);
        }

        const response = await fetch(endpoint, options);

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({ detail: response.statusText }));
            throw new Error(errorData.detail || 'An API error occurred.');
        }

        if (response.status === 204) { // No Content for successful DELETE
            return null;
        }

        return response.json();
    }

    const apiClient = {
        /**
         * API methods for Transactions.
         */
        transactions: {
            getAll: (params) => _request(`/api/transactions/?${params || ''}`),
            get: (id) => _request(`/api/transactions/${id}/`),
            create: (data) => _request('/api/transactions/', 'POST', data),
            update: (id, data) => _request(`/api/transactions/${id}/`, 'PATCH', data),
            delete: (id) => _request(`/api/transactions/${id}/`, 'DELETE'),
        },

        /**
         * API methods for Accounts.
         */
        accounts: {
            getAll: () => _request('/api/accounts/'),
            get: (id) => _request(`/api/accounts/${id}/`),
            create: (data) => _request('/api/accounts/', 'POST', data),
            update: (id, data) => _request(`/api/accounts/${id}/`, 'PATCH', data),
            delete: (id) => _request(`/api/accounts/${id}/`, 'DELETE'),
        },

        /**
         * API methods for Categories.
         */
        categories: {
            getAll: () => _request('/api/categories/'),
            get: (id) => _request(`/api/categories/${id}/`),
            create: (data) => _request('/api/categories/', 'POST', data),
            update: (id, data) => _request(`/api/categories/${id}/`, 'PATCH', data),
            delete: (id) => _request(`/api/categories/${id}/`, 'DELETE'),
        },
        
        /**
         * API methods for Budgets.
         */
        budgets: {
            getAll: () => _request('/api/budgets/'),
            get: (id) => _request(`/api/budgets/${id}/`),
            create: (data) => _request('/api/budgets/', 'POST', data),
            update: (id, data) => _request(`/api/budgets/${id}/`, 'PATCH', data),
            delete: (id) => _request(`/api/budgets/${id}/`, 'DELETE'),
        },

        /**
         * API methods for Subscriptions.
         */
        subscriptions: {
            getAll: () => _request('/api/subscriptions/'),
            get: (id) => _request(`/api/subscriptions/${id}/`),
            create: (data) => _request('/api/subscriptions/', 'POST', data),
            update: (id, data) => _request(`/api/subscriptions/${id}/`, 'PATCH', data),
            delete: (id) => _request(`/api/subscriptions/${id}/`, 'DELETE'),
        },

        /**
         * API methods for notifications
         */
        notifications: {
            getAll: () => _request('/api/notifications/'),
            get: (id) => _request(`/api/notifications/${id}/`),
            create: (data) => _request('/api/notifications/', 'POST', data),
            update: (id, data) => _request(`/api/notifications/${id}/`, 'PATCH', data),
            delete: (id) => _request(`/api/notifications/${id}/`, 'DELETE'),
            check: () => _request(`/api/notifications/check/`),
        },
        

        /**
         * Aggregated dashboard data using multiple API calls
         */
        getDashboardData: async (filters = {}) => {
            const params = new URLSearchParams(filters);
            return _request(`/api/dashboard/summary/?${params.toString()}`);
        }
    }

    // Attach the client to the window object to make it globally accessible
    window.apiClient = apiClient;

})(window);