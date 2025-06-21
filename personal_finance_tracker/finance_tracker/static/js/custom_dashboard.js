class ModernDashboard {
    constructor() {
        this.data = null;
        this.chart = null;
        this.refreshInterval = null;
        this.init();
    }

    async init() {
        
        // Set up event listeners
        this.setupEventListeners();
        
        // Load initial data
        await this.loadDashboardData();
        
        // Set up auto-refresh (every 5 minutes)
        this.setupAutoRefresh();
        
    }

    setupEventListeners() {
        // Filter form submission
        document.getElementById('filter-form').addEventListener('submit', (e) => {
            e.preventDefault();
            this.applyFilters();
        });

        // Clear filters button
        document.getElementById('clear-filters').addEventListener('click', () => {
            this.clearFilters();
        });

        // Refresh button
        document.getElementById('refresh-chart').addEventListener('click', () => {
            this.refreshData();
        });

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
            
            // Build query parameters
            const params = new URLSearchParams(filters);
            const response = await fetch(`/api/dashboard/?${params}`, {
                headers: {
                    'Accept': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const result = await response.json();
            
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
        
        // Update overview cards
        this.updateOverviewCards();
        
        // Update chart
        this.updateChart();
        
        // Update transactions list
        this.updateTransactionsList();
        
        // Update accounts list
        this.updateAccountsList();
        
        // Show dashboard content
        document.getElementById('dashboard-content').style.display = 'block';
    }

    updateOverviewCards() {
        const { financial_summary } = this.data;
        
        document.getElementById('total-income').textContent = 
            this.formatCurrency(financial_summary.total_income);
        document.getElementById('total-expenses').textContent = 
            this.formatCurrency(financial_summary.total_expenses);
        document.getElementById('net-balance').textContent = 
            this.formatCurrency(financial_summary.net_balance);
        document.getElementById('account-count').textContent = 
            financial_summary.account_count;

        // Update balance card color based on positive/negative
        const balanceCard = document.querySelector('.overview-card.balance');
        balanceCard.classList.remove('positive', 'negative');
        balanceCard.classList.add(financial_summary.net_balance >= 0 ? 'positive' : 'negative');
    }

    updateChart() {
        const ctx = document.getElementById('monthlyChart');
        if (!ctx) return;

        const { monthly_data } = this.data.chart_data;

        // Destroy existing chart
        if (this.chart) {
            this.chart.destroy();
        }

        // Create new chart
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
                                return `${context.dataset.label}: ${this.formatCurrency(context.parsed.y)}`;
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
        const container = document.getElementById('transactions-list');
        const { recent_transactions } = this.data;
    
        if (recent_transactions.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <i class="mdi mdi-inbox mdi-48px text-muted"></i>
                    <p class="text-muted">No transactions found</p>
                    <a href="/add-transaction/" class="btn btn-primary btn-sm">Add Transaction</a>
                </div>
            `;
            return;
        }
    
        container.innerHTML = recent_transactions.map(transaction => `
            <div class="transaction-item d-flex align-items-center justify-content-between" data-transaction-id="${transaction.id}">
                <div class="d-flex align-items-center">
                    <input type="checkbox" class="transaction-checkbox" value="${transaction.id}">
                    <div class="transaction-icon ${transaction.type}">
                        <i class="mdi mdi-${transaction.type === 'income' ? 'arrow-down' : 'arrow-up'}"></i>
                    </div>
                    <div class="transaction-details ms-2">
                        <div class="transaction-description">${transaction.description}</div>
                        <div class="transaction-meta">${transaction.date} • ${transaction.category}</div>
                    </div>
                </div>
                <div class="d-flex align-items-center gap-2">
                    <div class="transaction-amount ${transaction.type}">
                        ${transaction.type === 'income' ? '+' : '-'}${this.formatCurrency(transaction.amount)}
                    </div>
                    <a href="/update_transaction/${transaction.id}/?next=/dashboard/" class="btn btn-sm btn-outline-info" title="Edit">
                        <i class="mdi mdi-pencil"></i>
                    </a>
                    <button class="btn btn-sm btn-outline-danger delete-transaction-btn" data-transaction-id="${transaction.id}" title="Delete">
                        <i class="mdi mdi-delete"></i>
                    </button>
                </div>
            </div>
        `).join('');
    
        // Setup multi-select functionality
        this.setupMultiSelect();
        
        // Attach individual delete event listeners
        container.querySelectorAll('.delete-transaction-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const transactionId = btn.getAttribute('data-transaction-id');
                this.confirmAndDeleteTransaction([transactionId]);
            });
        });
    }
    
    setupMultiSelect() {
        const checkboxes = document.querySelectorAll('.transaction-checkbox');
        const selectAllBtn = document.getElementById('select-all-btn');
        const bulkDeleteBtn = document.getElementById('bulk-delete-btn');
        const selectedCountSpan = document.getElementById('selected-count');
    
        // Handle individual checkbox changes
        checkboxes.forEach(checkbox => {
            checkbox.addEventListener('change', () => {
                const item = checkbox.closest('.transaction-item');
                if (checkbox.checked) {
                    item.classList.add('selected');
                } else {
                    item.classList.remove('selected');
                }
                this.updateBulkActions();
            });
        });
    
        // Handle select all
        selectAllBtn.addEventListener('click', () => {
            const allChecked = Array.from(checkboxes).every(cb => cb.checked);
            checkboxes.forEach(checkbox => {
                checkbox.checked = !allChecked;
                const item = checkbox.closest('.transaction-item');
                if (checkbox.checked) {
                    item.classList.add('selected');
                } else {
                    item.classList.remove('selected');
                }
            });
            this.updateBulkActions();
        });
    
        // Handle bulk delete
        bulkDeleteBtn.addEventListener('click', () => {
            const selectedIds = Array.from(checkboxes)
                .filter(cb => cb.checked)
                .map(cb => cb.value);
            
            if (selectedIds.length > 0) {
                this.confirmAndDeleteTransaction(selectedIds);
            }
        });
    }
    
    updateBulkActions() {
        const checkboxes = document.querySelectorAll('.transaction-checkbox');
        const selectedCheckboxes = Array.from(checkboxes).filter(cb => cb.checked);
        const bulkDeleteBtn = document.getElementById('bulk-delete-btn');
        const selectedCountSpan = document.getElementById('selected-count');
        const selectAllBtn = document.getElementById('select-all-btn');
    
        const selectedCount = selectedCheckboxes.length;
        selectedCountSpan.textContent = selectedCount;
    
        if (selectedCount > 0) {
            bulkDeleteBtn.style.display = 'inline-block';
            selectAllBtn.innerHTML = '<i class="mdi mdi-checkbox-multiple-blank me-1"></i>Deselect All';
        } else {
            bulkDeleteBtn.style.display = 'none';
            selectAllBtn.innerHTML = '<i class="mdi mdi-checkbox-multiple-marked me-1"></i>Select All';
        }
    }
    
    confirmAndDeleteTransaction(transactionIds) {
        // Ensure transactionIds is always an array
        if (!Array.isArray(transactionIds)) {
            transactionIds = [transactionIds];
        }
    
        // Create modal if not exists
        let modal = document.getElementById('deleteTransactionModal');
        if (!modal) {
            modal = document.createElement('div');
            modal.id = 'deleteTransactionModal';
            modal.className = 'modal fade';
            modal.tabIndex = -1;
            modal.innerHTML = `
                <div class="modal-dialog">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">Confirm Deletion</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                        </div>
                        <div class="modal-body" id="deleteModalBody">
                            <!-- Content will be updated dynamically -->
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                            <button type="button" class="btn btn-danger" id="confirmDeleteTransactionBtn">Delete</button>
                        </div>
                    </div>
                </div>
            `;
            document.body.appendChild(modal);
        }
    
        // Update modal content based on selection count
        const modalBody = modal.querySelector('#deleteModalBody');
        if (transactionIds.length === 1) {
            modalBody.innerHTML = 'Are you sure you want to delete this transaction? This action cannot be undone.';
        } else {
            modalBody.innerHTML = `Are you sure you want to delete ${transactionIds.length} transactions? This action cannot be undone.`;
        }
    
        // Show modal
        const bsModal = new bootstrap.Modal(modal);
        bsModal.show();
    
        // Attach confirm handler
        const confirmBtn = modal.querySelector('#confirmDeleteTransactionBtn');
        confirmBtn.onclick = () => {
            confirmBtn.disabled = true;
            const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
            
            // Send as comma-separated list like your backend expects
            const formData = new URLSearchParams();
            transactionIds.forEach(id => formData.append('transaction_ids', id));
            formData.append('confirm', '1');
    
            fetch('/delete-transactions/', {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrfToken,
                    'X-Requested-With': 'XMLHttpRequest',
                    'Content-Type': 'application/x-www-form-urlencoded'
                },
                body: formData.toString()
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }
                return response.json();
            })
            .then(data => {
                if (data.status === 'success') {
                    // Refresh dashboard data to update totals
                    this.refreshData();

                    // Clear all checkboxes and reset bulk actions
                    const checkboxes = document.querySelectorAll('.transaction-checkbox');
                    checkboxes.forEach(checkbox => {
                        checkbox.checked = false;
                        const item = checkbox.closest('.transaction-item');
                        if (item) item.classList.remove('selected');
                    });
                    this.updateBulkActions();

                    this.showSuccess(data.message || `${transactionIds.length} transaction(s) deleted successfully.`);
                } else {
                    this.showError(data.message || 'Failed to delete transactions.');
                }
                bsModal.hide();
            })
            .catch(error => {
                console.error('Error:', error);
                this.showError('Error deleting transactions.');
                bsModal.hide();
            })
            .finally(() => {
                confirmBtn.disabled = false;
            });
        };
    }
    
    // Add this method if you don't have it
    showSuccess(message) {
        const toast = document.createElement('div');
        toast.className = 'alert alert-success alert-dismissible fade show position-fixed';
        toast.style.cssText = 'top: 20px; right: 20px; z-index: 9999; max-width: 400px;';
        toast.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        document.body.appendChild(toast);
        
        setTimeout(() => {
            if (toast.parentNode) {
                toast.parentNode.removeChild(toast);
            }
        }, 3000);
    }

    updateAccountsList() {
        const container = document.getElementById('accounts-list');
        const { accounts } = this.data;

        if (accounts.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <i class="mdi mdi-bank-outline mdi-36px text-muted"></i>
                    <p class="text-muted">No accounts added</p>
                    <a href="/manage-bank-accounts/" class="btn btn-primary btn-sm">Add Account</a>
                </div>
            `;
            return;
        }

        container.innerHTML = accounts.map(account => `
            <div class="account-item">
                <div class="account-info">
                    <div class="account-name">${account.account_number}</div>
                    <div class="account-type">${account.account_type}</div>
                </div>
                <div class="account-balance">${this.formatCurrency(account.balance)}</div>
            </div>
        `).join('');
    }

    async applyFilters() {
        const filters = {
            type: document.getElementById('filter-type').value,
            category: document.getElementById('filter-category').value,
            start: document.getElementById('filter-start').value,
            end: document.getElementById('filter-end').value
        };

        // Remove empty filters
        Object.keys(filters).forEach(key => {
            if (!filters[key]) delete filters[key];
        });

        await this.loadDashboardData(filters);
    }

    clearFilters() {
        document.getElementById('filter-form').reset();
        this.loadDashboardData();
    }

    async refreshData() {
        console.log('Refreshing dashboard data...');
        
        // Get current filters
        const filters = {};
        const formData = new FormData(document.getElementById('filter-form'));
        for (let [key, value] of formData.entries()) {
            if (value) filters[key] = value;
        }
        
        await this.loadDashboardData(filters);
    }

    setupAutoRefresh() {
        // Refresh every 5 minutes when page is visible
        this.refreshInterval = setInterval(() => {
            if (!document.hidden) {
                this.refreshData();
            }
        }, 5 * 60 * 1000); // 5 minutes
    }

    showLoading() {
        document.getElementById('loading-indicator').style.display = 'flex';
    }

    hideLoading() {
        document.getElementById('loading-indicator').style.display = 'none';
    }

    showError(message) {
        // Create toast notification for errors
        const toast = document.createElement('div');
        toast.className = 'alert alert-danger alert-dismissible fade show position-fixed';
        toast.style.cssText = 'top: 20px; right: 20px; z-index: 9999; max-width: 400px;';
        toast.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        document.body.appendChild(toast);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (toast.parentNode) {
                toast.parentNode.removeChild(toast);
            }
        }, 5000);
    }

    formatCurrency(amount) {
        return new Intl.NumberFormat('en-CA', {
            style: 'currency',
            currency: 'CAD'
        }).format(amount);
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
document.addEventListener('DOMContentLoaded', () => {
    window.dashboard = new ModernDashboard();
});

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
    if (window.dashboard) {
        window.dashboard.destroy();
    }
});