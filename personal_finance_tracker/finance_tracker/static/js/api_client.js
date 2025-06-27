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
            /**
             * Get a list of all transactions, with optional filters.
             * @param {URLSearchParams} [params] - Optional query parameters for filtering.
             * @returns {Promise<Array>}
             */
            getAll: (params) => _request(`/api/transactions/?${params || ''}`),

            /**
             * Get a single transaction by its ID.
             * @param {number} id - The transaction ID.
             * @returns {Promise<Object>}
             */
            get: (id) => _request(`/api/transactions/${id}/`),

            /**
             * Create a new transaction.
             * @param {Object} data - The transaction data.
             * @returns {Promise<Object>}
             */
            create: (data) => _request('/api/transactions/', 'POST', data),

            /**
             * Update an existing transaction.
             * @param {number} id - The transaction ID.
             * @param {Object} data - The data to update.
             * @returns {Promise<Object>}
             */
            update: (id, data) => _request(`/api/transactions/${id}/`, 'PATCH', data),

            /**
             * Delete a transaction.
             * @param {number} id - The transaction ID.
             * @returns {Promise<null>}
             */
            delete: (id) => _request(`/api/transactions/${id}/`, 'DELETE'),
        },

        /**
         * API methods for Accounts.
         * (You can expand this with get, create, update, delete methods)
         */
        accounts: {
            getAll: () => _request('/api/accounts/'),
        },

        /**
         * API methods for Categories.
         */
        categories: {
            getAll: () => _request('/api/categories/'),
        },
        
        /**
         * API methods for Budgets.
         */
        budgets: {
            getAll: () => _request('/api/budgets/'),
        },

        /**
         * API methods for Subscriptions.
         */
        subscriptions: {
            getAll: () => _request('/api/subscriptions/'),
        },

        /**
         * Custom endpoint for aggregated dashboard data.
         */
        getDashboardData: (filters) => {
            const params = new URLSearchParams(filters);
            return _request(`/api/dashboard/?${params.toString()}`);
        }
    };

    // Attach the client to the window object to make it globally accessible
    window.apiClient = apiClient;

})(window);