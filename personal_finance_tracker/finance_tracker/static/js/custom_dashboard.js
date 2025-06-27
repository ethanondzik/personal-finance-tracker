function DashboardManager() {
    this.data = null;
    this.chart = null;
    this.refreshInterval = null;
    
    // Initialize dashboard
    this.init = function() {
        this.setupEventListeners();
        this.loadDashboardData();
        this.setupAutoRefresh();
    };

    this.setupEventListeners = function() {
        var self = this;
        
        // Refresh button
        var refreshBtn = document.getElementById('refresh-dashboard');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', function() {
                self.loadDashboardData();
            });
        }

        // Auto-refresh on visibility change
        document.addEventListener('visibilitychange', function() {
            if (!document.hidden) {
                self.refreshData();
            }
        });
    };

    this.loadDashboardData = function(filters) {
        var self = this;
        filters = filters || {};
        
        try {
            self.showLoading();
            
            var params = new URLSearchParams(filters);
            fetch('/api/dashboard/?' + params.toString(), {
                headers: {
                    'Accept': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(function(response) {
                if (!response.ok) {
                    throw new Error('HTTP ' + response.status + ': ' + response.statusText);
                }
                return response.json();
            })
            .then(function(result) {
                if (result.status === 'success') {
                    self.data = result.data;
                    self.updateDashboard();
                } else {
                    throw new Error(result.message || 'Failed to load dashboard data');
                }
            })
            .catch(function(error) {
                console.error('Error loading dashboard data:', error);
                self.showError('Failed to load dashboard data. Please try again.');
            })
            .finally(function() {
                self.hideLoading();
            });
            
        } catch (error) {
            console.error('Error loading dashboard data:', error);
            self.showError('Failed to load dashboard data. Please try again.');
            self.hideLoading();
        }
    };

    this.updateDashboard = function() {
        if (!this.data) return;
        
        this.updateOverviewCards();
        this.updateChart();
        this.updateTransactionsList();
        this.updateSubscriptionsCard();
        this.updateBudgetsCard();
        
        // Show dashboard content
        var dashboardContent = document.getElementById('dashboard-content');
        if (dashboardContent) {
            dashboardContent.style.display = 'block';
        }
    };

    this.updateOverviewCards = function() {
        var financial_summary = this.data.financial_summary;
        
        this.updateElement('total-income', this.formatCurrency(financial_summary.total_income));
        this.updateElement('total-expenses', this.formatCurrency(financial_summary.total_expenses));
        this.updateElement('net-balance', this.formatCurrency(financial_summary.net_balance));
        this.updateElement('account-count', financial_summary.account_count);
        
        // Update balance card color
        var balanceCard = document.querySelector('.overview-card.balance');
        if (balanceCard) {
            balanceCard.classList.remove('positive', 'negative');
            balanceCard.classList.add(financial_summary.net_balance >= 0 ? 'positive' : 'negative');
        }
    };

    this.updateChart = function() {
        var ctx = document.getElementById('monthlyChart');
        if (!ctx) return;
        
        var monthly_data = this.data.chart_data.monthly_data;
        
        // Make sure ref to previous chart is not lost and delete it before proceeding
        var existingChart = Chart.getChart(ctx);
        if (existingChart) {
            existingChart.destroy();
        }
        
        var self = this;
        this.chart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: monthly_data.map(function(item) { return item.month; }),
                datasets: [{
                    label: 'Income',
                    data: monthly_data.map(function(item) { return item.income; }),
                    backgroundColor: 'rgba(76, 175, 80, 0.8)',
                    borderColor: '#4CAF50',
                    borderWidth: 1,
                    borderRadius: 8,
                }, {
                    label: 'Expenses',
                    data: monthly_data.map(function(item) { return item.expenses; }),
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
                            callback: function(value) {
                                return self.formatCurrency(value);
                            }
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
                            label: function(context) {
                                return context.dataset.label + ': ' + self.formatCurrency(context.parsed.y);
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
    };

    this.updateTransactionsList = function() {
        var container = document.getElementById('recent-transactions-list');
        if (!container) return;

        var recent_transactions = this.data.recent_transactions;
        var self = this;
        
        if (recent_transactions.length === 0) {
            container.innerHTML = '<div class="text-center py-4 text-muted"><i class="bi bi-inbox fs-1"></i><p class="mt-2">No recent transactions</p><a href="/add-transaction/" class="btn btn-primary btn-sm">Add Transaction</a></div>';
            return;
        }
        
        container.innerHTML = recent_transactions.map(function(transaction) {
            return '<div class="transaction-item d-flex align-items-center justify-content-between">' +
                '<div class="d-flex align-items-center">' +
                    '<div class="transaction-icon ' + transaction.transaction_type + '">' +
                        '<i class="bi ' + (transaction.transaction_type === 'income' ? 'bi-arrow-down-left' : 'bi-arrow-up-right') + '"></i>' +
                    '</div>' +
                    '<div class="transaction-details ms-3">' +
                        '<div class="transaction-description">' + transaction.description + '</div>' +
                        '<div class="transaction-meta">' +
                            transaction.category + ' • ' + new Date(transaction.date).toLocaleDateString() +
                        '</div>' +
                    '</div>' +
                '</div>' +
                '<div class="d-flex align-items-center gap-2">' +
                    '<div class="transaction-amount ' + transaction.transaction_type + '">' +
                        (transaction.transaction_type === 'income' ? '+' : '-') + self.formatCurrency(Math.abs(transaction.amount)) +
                    '</div>' +
                    '<a href="/update_transaction/' + transaction.id + '/?next=/dashboard/" class="btn btn-sm btn-outline-info" title="Edit">' +
                        '<i class="bi bi-pencil"></i>' +
                    '</a>' +
                    '<button class="btn btn-sm btn-outline-danger delete-transaction-btn" data-transaction-id="' + transaction.id + '" title="Delete">' +
                        '<i class="bi bi-trash"></i>' +
                    '</button>' +
                '</div>' +
            '</div>';
        }).join('');
        
        // Setup delete transaction handlers
        this.setupTransactionDeleteHandlers();
    };

    this.updateSubscriptionsCard = function() {
        var subscriptions = this.data.subscriptions;
        
        this.updateElement('subscriptions-count', subscriptions ? subscriptions.total || 0 : 0);
        
        var nextDueElement = document.getElementById('subscriptions-next-due');
        if (nextDueElement) {
            if (subscriptions && subscriptions.next_due_date && subscriptions.next_due_name) {
                var date = new Date(subscriptions.next_due_date);
                nextDueElement.textContent = 'Next: ' + subscriptions.next_due_name + ' (' + date.toLocaleDateString() + ')';
            } else {
                nextDueElement.textContent = 'No upcoming payments';
            }
        }
        
        var listContainer = document.getElementById('subscriptions-list');
        if (listContainer) {
            if (!subscriptions || !subscriptions.preview || subscriptions.preview.length === 0) {
                listContainer.innerHTML = '<li class="text-muted">No active subscriptions</li>';
                return;
            }
            
            var self = this;
            listContainer.innerHTML = subscriptions.preview.map(function(sub) {
                return '<li>' +
                    '<div>' +
                        '<span class="fw-semibold">' + sub.name + '</span>' +
                        '<small class="text-muted d-block">Due: ' + new Date(sub.next_payment_date).toLocaleDateString() + '</small>' +
                    '</div>' +
                    '<span class="text-muted">' + self.formatCurrency(sub.amount) + '</span>' +
                '</li>';
            }).join('');
        }
    };

    this.updateBudgetsCard = function() {
        var budgets = this.data.budgets;
        
        this.updateElement('total-budget-amount', this.formatCurrency(budgets ? budgets.total_budget_amount || 0 : 0));
        this.updateElement('total-spent-amount', this.formatCurrency(budgets ? budgets.total_spent || 0 : 0));
        
        var totalBudget = budgets ? budgets.total_budget_amount || 0 : 0;
        var totalSpent = budgets ? budgets.total_spent || 0 : 0;
        var percentage = totalBudget > 0 ? (totalSpent / totalBudget) * 100 : 0;
        
        var progressBar = document.getElementById('budget-progress-bar');
        if (progressBar) {
            progressBar.style.width = Math.min(percentage, 100) + '%';
            progressBar.setAttribute('aria-valuenow', percentage);
            
            progressBar.className = 'progress-bar';
            if (percentage > 100) {
                progressBar.classList.add('bg-danger');
            } else if (percentage > 80) {
                progressBar.classList.add('bg-warning');
            } else {
                progressBar.classList.add('bg-success');
            }
        }
    };

    this.setupTransactionDeleteHandlers = function() {
        var self = this;
        var deleteButtons = document.querySelectorAll('.delete-transaction-btn');
        deleteButtons.forEach(function(btn) {
            btn.addEventListener('click', function(e) {
                e.stopPropagation();
                var transactionId = btn.getAttribute('data-transaction-id');
                self.confirmDeleteTransaction(transactionId);
            });
        });
    };

    this.confirmDeleteTransaction = function(transactionId) {
        if (confirm('Are you sure you want to delete this transaction?')) {
            this.deleteTransaction(transactionId);
        }
    };

    this.deleteTransaction = function(transactionId) {
        var self = this;
        try {
            fetch('/delete-transactions/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'X-CSRFToken': getCSRFToken()
                },
                body: 'transaction_ids=' + transactionId + '&confirm=1'
            })
            .then(function(response) {
                return response.json();
            })
            .then(function(result) {
                if (result.status === 'success') {
                    if (window.showNotification) {
                        window.showNotification('Transaction deleted successfully', 'success');
                    }
                    self.loadDashboardData(); // Refresh data
                } else {
                    throw new Error(result.message || 'Failed to delete transaction');
                }
            })
            .catch(function(error) {
                console.error('Error deleting transaction:', error);
                if (window.showNotification) {
                    window.showNotification('Error deleting transaction', 'danger');
                }
            });
        } catch (error) {
            console.error('Error deleting transaction:', error);
            if (window.showNotification) {
                window.showNotification('Error deleting transaction', 'danger');
            }
        }
    };

    this.refreshData = function() {
        console.log('Refreshing dashboard data...');
        this.loadDashboardData();
    };

    this.setupAutoRefresh = function() {
        var self = this;
        this.refreshInterval = setInterval(function() {
            if (!document.hidden) {
                self.refreshData();
            }
        }, 5 * 60 * 1000); // 5 minutes
    };

    // Utility methods
    this.updateElement = function(id, value) {
        var element = document.getElementById(id);
        if (element) {
            element.textContent = value;
        }
    };

    this.formatCurrency = function(amount) {
        return new Intl.NumberFormat('en-CA', {
            style: 'currency',
            currency: 'CAD'
        }).format(amount);
    };

    this.showLoading = function() {
        var loading = document.getElementById('loading-indicator');
        if (loading) {
            loading.style.display = 'flex';
        }
    };

    this.hideLoading = function() {
        var loading = document.getElementById('loading-indicator');
        if (loading) {
            loading.style.display = 'none';
        }
    };

    this.showError = function(message) {
        if (window.showNotification) {
            window.showNotification(message, 'danger');
        }
    };

    this.destroy = function() {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
        }
        if (this.chart) {
            this.chart.destroy();
        }
    };
}

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    if (window.dashboardManager) {
        window.dashboardManager.destroy();
    }

    window.dashboardManager = new DashboardManager();
    window.dashboardManager.init();
});

// Cleanup on page unload
window.addEventListener('beforeunload', function() {
    if (window.dashboardManager) {
        window.dashboardManager.destroy();
    }
});