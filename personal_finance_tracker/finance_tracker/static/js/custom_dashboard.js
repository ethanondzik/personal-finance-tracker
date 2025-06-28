class Dashboard {
    constructor() {
        this.data = null;
        this.chart = null;
        this.refreshInterval = null;
    }

    async init() {
        try {
            this.showLoading();
            this.setupEventListeners();
            await this.loadDashboardData();
            this.updateDashboard();
            this.setupAutoRefresh();
        } catch (error) {
            console.error('Dashboard initialization error:', error);
            this.showError('Failed to load dashboard data');
        } finally {
            this.hideLoading();
        }
    }

    setupEventListeners() {
        // Refresh button
        const refreshBtn = document.getElementById('refresh-dashboard');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => {
                this.refreshData();
            });
        }

        // Auto-refresh on visibility change
        document.addEventListener('visibilitychange', () => {
            if (!document.hidden) {
                this.refreshData();
            }
        });
    }

    async loadDashboardData(filters = {}) {
        try {
            this.showLoading();
            
            // Use the API client instead of manual fetch
            const result = await apiClient.getDashboardData(filters);
            
            if (result.status === 'success') {
                this.data = result.data;
                this.updateDashboard();
            } else {
                throw new Error(result.message || 'Failed to load dashboard data');
            }
        } catch (error) {
            console.error('Error loading dashboard data:', error);
            this.showError('Failed to load dashboard data. Please try again.');
        } finally {
            this.hideLoading();
        }
    }

    updateDashboard() {
        if (!this.data) return;
        
        this.updateOverviewCards();
        this.updateChart();
        this.updateTransactionsList();
        this.updateAccountsList();
        this.updateBudgets();
        this.updateSubscriptions();
        
        // Show dashboard content
        const dashboardContent = document.getElementById('dashboard-content');
        if (dashboardContent) {
            dashboardContent.style.display = 'block';
        }
    }

    updateOverviewCards() {
        const { financial_summary } = this.data;
        
        this.updateElement('total-income', this.formatCurrency(financial_summary.total_income));
        this.updateElement('total-expenses', this.formatCurrency(financial_summary.total_expenses));
        this.updateElement('net-balance', this.formatCurrency(financial_summary.net_balance));
        this.updateElement('account-count', financial_summary.account_count);
        
        // Update balance card color
        const balanceCard = document.querySelector('.overview-card.balance');
        if (balanceCard) {
            balanceCard.classList.remove('positive', 'negative');
            balanceCard.classList.add(financial_summary.net_balance >= 0 ? 'positive' : 'negative');
        }
    }

    updateChart() {
        const ctx = document.getElementById('monthlyChart');
        if (!ctx) return;
        
        const { monthly_data } = this.data.chart_data;
        
        // Destroy existing chart
        const existingChart = Chart.getChart(ctx);
        if (existingChart) {
            existingChart.destroy();
        }
        
        this.chart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: monthly_data.map(item => item.month),
                datasets: [{
                    label: 'Income',
                    data: monthly_data.map(item => item.income),
                    backgroundColor: 'rgba(76, 175, 80, 0.8)',
                    borderColor: '#4CAF50',
                    borderWidth: 1,
                    borderRadius: 8,
                }, {
                    label: 'Expenses',
                    data: monthly_data.map(item => item.expenses),
                    backgroundColor: 'rgba(244, 67, 54, 0.8)',
                    borderColor: '#f44336',
                    borderWidth: 1,
                    borderRadius: 8,
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: {
                    mode: 'index',
                    intersect: false,
                },
                scales: {
                    x: {
                        grid: { display: false }
                    },
                    y: {
                        beginAtZero: true,
                        ticks: {
                            callback: (value) => this.formatCurrency(value)
                        }
                    }
                },
                plugins: {
                    legend: {
                        position: 'top',
                        labels: {
                            usePointStyle: true,
                            pointStyle: 'circle'
                        }
                    },
                    tooltip: {
                        callbacks: {
                            label: (context) => {
                                return context.dataset.label + ': ' + this.formatCurrency(context.parsed.y);
                            }
                        }
                    }
                },
                animation: {
                    duration: 1000,
                    easing: 'easeInOutQuart'
                }
            }
        });
    }

    updateTransactionsList() {
        const container = document.getElementById('recent-transactions-list');
        if (!container) return;

        const { recent_transactions } = this.data;
        
        if (recent_transactions.length === 0) {
            container.innerHTML = `
                <div class="text-center py-4 text-muted">
                    <i class="bi bi-inbox fs-1"></i>
                    <p class="mt-2">No recent transactions</p>
                    <a href="/add-transaction/" class="btn btn-primary btn-sm">Add Transaction</a>
                </div>
            `;
            return;
        }
        
        container.innerHTML = recent_transactions.map(transaction => `
            <div class="transaction-item d-flex align-items-center justify-content-between p-3 border-bottom" data-transaction-id="${transaction.id}">
                <div class="d-flex align-items-center">
                    <div class="transaction-icon ${transaction.type} me-3">
                        <i class="bi ${transaction.type === 'income' ? 'bi-arrow-down-left' : 'bi-arrow-up-right'}"></i>
                    </div>
                    <div class="transaction-details">
                        <div class="transaction-description fw-semibold">${transaction.description}</div>
                        <div class="transaction-meta text-muted small">
                            ${transaction.category} • ${new Date(transaction.date).toLocaleDateString()}
                        </div>
                    </div>
                </div>
                <div class="d-flex align-items-center gap-2">
                    <div class="transaction-amount ${transaction.type} fw-bold">
                        ${transaction.type === 'income' ? '+' : '-'}${this.formatCurrency(Math.abs(transaction.amount))}
                    </div>
                    <button class="btn btn-sm btn-outline-info" onclick="window.location.href='/update_transaction/${transaction.id}/?next=/dashboard/'" title="Edit">
                        <i class="bi bi-pencil"></i>
                    </button>
                    <button class="btn btn-sm btn-outline-danger delete-transaction-btn" data-transaction-id="${transaction.id}" title="Delete">
                        <i class="bi bi-trash"></i>
                    </button>
                </div>
            </div>
        `).join('');
        
        // Setup delete transaction handlers
        this.setupTransactionDeleteHandlers();
    }

    updateAccountsList() {
        const container = document.getElementById('account-summary-list');
        if (!container) return;

        const { accounts } = this.data;
        
        if (accounts.length === 0) {
            container.innerHTML = `
                <div class="text-center p-3 text-muted">
                    <i class="bi bi-bank"></i>
                    <p>No accounts found</p>
                    <a href="/manage-bank-accounts/" class="btn btn-primary btn-sm">Add Account</a>
                </div>
            `;
            return;
        }
        
        container.innerHTML = accounts.map(account => `
            <div class="account-item d-flex justify-content-between align-items-center py-2 border-bottom">
                <div>
                    <div class="fw-semibold">${account.account_number}</div>
                    <small class="text-muted">${account.account_type}</small>
                </div>
                <div class="fw-bold">${this.formatCurrency(account.balance)}</div>
            </div>
        `).join('');
    }

    updateBudgets() {
        const { budgets } = this.data;
        
        // Update budget summary
        this.updateElement('total-budget-amount', this.formatCurrency(budgets.total_budget_amount));
        this.updateElement('total-spent-amount', this.formatCurrency(budgets.total_spent));
        
        // Update progress bar
        const overallPercentage = budgets.total_budget_amount > 0 
            ? (budgets.total_spent / budgets.total_budget_amount) * 100 
            : 0;
        
        const progressBar = document.getElementById('budget-progress-bar');
        if (progressBar) {
            progressBar.style.width = `${Math.min(overallPercentage, 100)}%`;
            progressBar.className = 'progress-bar';
            
            if (overallPercentage > 100) {
                progressBar.classList.add('bg-danger');
            } else if (overallPercentage > 80) {
                progressBar.classList.add('bg-warning');
            } else {
                progressBar.classList.add('bg-success');
            }
        }
        
        // Update budget items
        const container = document.getElementById('budget-items-container');
        if (container) {
            if (budgets.budget_items.length === 0) {
                container.innerHTML = `
                    <div class="empty-state text-center">
                        <i class="bi bi-wallet2"></i>
                        <p class="text-muted">No budgets set</p>
                        <a href="/manage-budgets/" class="btn btn-primary btn-sm">Create Budget</a>
                    </div>
                `;
                return;
            }
            
            container.innerHTML = budgets.budget_items.map(budget => `
                <div class="budget-item mb-3">
                    <div class="d-flex justify-content-between mb-1">
                        <span class="fw-semibold">${budget.category_name}</span>
                        <span class="text-muted">${this.formatCurrency(budget.spent)} / ${this.formatCurrency(budget.amount)}</span>
                    </div>
                    <div class="progress mb-1" style="height: 6px;">
                        <div class="progress-bar ${this.getBudgetProgressClass(budget.status)}" 
                             style="width: ${Math.min(budget.percentage_used, 100)}%"></div>
                    </div>
                    <div class="d-flex justify-content-between">
                        <small class="text-muted">${budget.percentage_used}% used</small>
                        <small class="text-${budget.status === 'over' ? 'danger' : 'muted'}">
                            ${budget.remaining >= 0 ? this.formatCurrency(budget.remaining) + ' left' : this.formatCurrency(Math.abs(budget.remaining)) + ' over'}
                        </small>
                    </div>
                </div>
            `).join('');
        }
    }

    updateSubscriptions() {
        const { subscriptions } = this.data;
        const container = document.getElementById('subscriptions-list');
        
        if (!container) return;
        
        if (subscriptions.total === 0) {
            container.innerHTML = '<li class="list-group-item text-muted">No active subscriptions</li>';
            return;
        }
        
        // You'll need to add subscription preview data to your API
        container.innerHTML = `
            <li class="list-group-item d-flex justify-content-between">
                <span>Total Active</span>
                <span class="fw-bold">${subscriptions.active}</span>
            </li>
            ${subscriptions.next_due_name ? `
            <li class="list-group-item">
                <div class="d-flex justify-content-between">
                    <span>Next Due</span>
                    <span class="text-muted">${new Date(subscriptions.next_due_date).toLocaleDateString()}</span>
                </div>
                <small class="text-muted">${subscriptions.next_due_name}</small>
            </li>
            ` : ''}
        `;
    }

    setupTransactionDeleteHandlers() {
        const deleteButtons = document.querySelectorAll('.delete-transaction-btn');
        deleteButtons.forEach(btn => {
            btn.addEventListener('click', async (e) => {
                e.stopPropagation();
                const transactionId = btn.getAttribute('data-transaction-id');
                await this.deleteTransaction(transactionId);
            });
        });
    }

    async deleteTransaction(transactionId) {
        if (!confirm('Are you sure you want to delete this transaction?')) {
            return;
        }

        try {
            // Using the existing delete endpoint instead of the API client 
            // since it's a custom multi-delete endpoint
            const response = await fetch('/delete-transactions/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: `transaction_ids=${transactionId}&confirm=1`
            });

            const result = await response.json();
            
            if (result.status === 'success') {
                this.showSuccess('Transaction deleted successfully');
                await this.loadDashboardData(); // Refresh data
            } else {
                throw new Error(result.message || 'Failed to delete transaction');
            }
        } catch (error) {
            console.error('Error deleting transaction:', error);
            this.showError('Error deleting transaction');
        }
    }

    async refreshData() {
        console.log('Refreshing dashboard data...');
        await this.loadDashboardData();
    }

    setupAutoRefresh() {
        this.refreshInterval = setInterval(() => {
            if (!document.hidden) {
                this.refreshData();
            }
        }, 5 * 60 * 1000); // 5 minutes
    }

    // Utility methods
    updateElement(id, value) {
        const element = document.getElementById(id);
        if (element) {
            element.textContent = value;
        }
    }

    formatCurrency(amount) {
        return new Intl.NumberFormat('en-CA', {
            style: 'currency',
            currency: 'CAD'
        }).format(amount);
    }

    getBudgetProgressClass(status) {
        switch(status) {
            case 'good': return 'bg-success';
            case 'warning': return 'bg-warning';
            case 'over': return 'bg-danger';
            default: return 'bg-primary';
        }
    }

    getCSRFToken() {
        const cookieValue = document.cookie
            .split('; ')
            .find(row => row.startsWith('csrftoken='))
            ?.split('=')[1];
        return cookieValue || '';
    }

    showLoading() {
        const loading = document.getElementById('loading-indicator');
        if (loading) {
            loading.style.display = 'flex';
        }
    }

    hideLoading() {
        const loading = document.getElementById('loading-indicator');
        if (loading) {
            loading.style.display = 'none';
        }
    }

    showError(message) {
        console.error(message);
        // You can implement a toast notification system here
        alert(message); // Temporary fallback
    }

    showSuccess(message) {
        console.log(message);
        // You can implement a toast notification system here
        // Temporary fallback - could use a toast library
    }

    destroy() {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
        }
        if (this.chart) {
            this.chart.destroy();
        }
    }
}

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    if (window.dashboard) {
        window.dashboard.destroy();
    }

    window.dashboard = new Dashboard();
    window.dashboard.init();
});

// Cleanup on page unload
window.addEventListener('beforeunload', function() {
    if (window.dashboard) {
        window.dashboard.destroy();
    }
});