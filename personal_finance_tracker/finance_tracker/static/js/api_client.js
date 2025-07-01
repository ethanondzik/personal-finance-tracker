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
            getAll: (options = {}) => {
                const {
                    // Pagination
                    page = 1,
                    page_size = 25,
                    
                    // Ordering
                    ordering = '-date',
                    
                    // Search
                    search = '',
                    
                    // Date filtering
                    start_date = '',
                    end_date = '',
                    date_range = '',
                    date_year = '',
                    date_month = '',
                    
                    // Amount filtering
                    min_amount = '',
                    max_amount = '',
                    amount_range = '',
                    
                    // Category/Account filtering
                    category = '',
                    category_type = '',
                    account = '',
                    account_type = '',
                    
                    // Transaction specifics
                    transaction_type = '',
                    method = '',
                    
                    // Field selection
                    fields = '',
                    
                    // Boolean filters
                    has_category = '',
                    has_account = ''
                } = options;
                
                const params = new URLSearchParams();
                
                // Add all parameters if they have values
                if (page) params.append('page', page);
                if (page_size) params.append('page_size', page_size);
                if (ordering) params.append('ordering', ordering);
                if (search) params.append('search', search);
                if (start_date) params.append('start_date', start_date);
                if (end_date) params.append('end_date', end_date);
                if (date_range) params.append('date_range', date_range);
                if (date_year) params.append('date_year', date_year);
                if (date_month) params.append('date_month', date_month);
                if (min_amount) params.append('min_amount', min_amount);
                if (max_amount) params.append('max_amount', max_amount);
                if (amount_range) params.append('amount_range', amount_range);
                if (category) params.append('category', category);
                if (category_type) params.append('category_type', category_type);
                if (account) params.append('account', account);
                if (account_type) params.append('account_type', account_type);
                if (transaction_type) params.append('transaction_type', transaction_type);
                if (method) params.append('method', method);
                if (fields) params.append('fields', fields);
                if (has_category !== '') params.append('has_category', has_category);
                if (has_account !== '') params.append('has_account', has_account);
                
                return _request(`/api/transactions/?${params.toString()}`);
            },

            // Get summary statistics
            getSummary: (filters = {}) => {
                const params = new URLSearchParams(filters);
                return _request(`/api/transactions/summary/?${params.toString()}`);
            },

            // Export transactions
            export: (filters = {}) => {
                const params = new URLSearchParams(filters);
                window.open(`/api/transactions/export/?${params.toString()}`);
            },

            // Get available fields
            getFields: () => _request('/api/transactions/fields/'),

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