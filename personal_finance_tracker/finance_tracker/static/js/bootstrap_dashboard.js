// Theme Toggle Functionality
document.addEventListener('DOMContentLoaded', function() {
    const themeToggle = document.getElementById('themeToggle');
    const themeIcon = document.getElementById('themeIcon');
    const themeText = document.getElementById('themeText');
    
    const html = document.documentElement;
    
    if (themeToggle) {
        themeToggle.addEventListener('click', function() {
            const currentTheme = html.getAttribute('data-bs-theme');
            const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
            
            // Apply theme immediately to prevent flash
            html.setAttribute('data-bs-theme', newTheme);
            document.body.className = document.body.className.replace(/\b(light-theme|dark-theme)\b/g, '');
            document.body.classList.add(newTheme + '-theme');
            
            // Save to database only
            fetch('/update-theme-preference/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'X-CSRFToken': getCSRFToken()
                },
                body: 'theme=' + encodeURIComponent(newTheme)
            });
        });
    }
    
    function updateThemeUI(theme) {
        if (theme === 'dark') {
            themeIcon.className = 'bi bi-moon-fill me-2';
            themeText.textContent = 'Switch Light Mode';
        } else {
            themeIcon.className = 'bi bi-sun-fill me-2';
            themeText.textContent = 'Dark Mode';
        }
    }
    
    function getCSRFToken() {
        const cookieValue = document.cookie
            .split('; ')
            .find(row => row.startsWith('csrftoken='));
        return cookieValue ? cookieValue.split('=')[1] : '';
    }
    
    // Sidebar Toggle for Mobile
    const sidebarToggle = document.getElementById('sidebarToggle');
    const sidebar = document.getElementById('sidebar');
    const sidebarBackdrop = document.getElementById('sidebarBackdrop');
    
    if (sidebarToggle) {
        sidebarToggle.addEventListener('click', function() {
            sidebar.classList.toggle('show');
            sidebarBackdrop.classList.toggle('show');
        });
    }
    
    if (sidebarBackdrop) {
        sidebarBackdrop.addEventListener('click', function() {
            sidebar.classList.remove('show');
            sidebarBackdrop.classList.remove('show');
        });
    }
    
    // Desktop Sidebar Collapse (optional)
    const sidebarCollapseBtn = document.getElementById('sidebarCollapseDesktop');
    if (sidebarCollapseBtn) {
        sidebarCollapseBtn.addEventListener('click', function() {
            document.body.classList.toggle('sidebar-collapsed');
        });
    }
});

// Dashboard Data Management
class BootstrapDashboard {
    constructor() {
        this.data = null;
        this.chart = null;
        this.init();
    }
    
    async init() {
        await this.loadDashboardData();
        this.setupEventListeners();
    }
    
    async loadDashboardData() {
        try {
            this.showLoading();
            const response = await fetch('/api/dashboard/');
            const result = await response.json();
            
            if (result.status === 'success') {
                this.data = result.data;
                this.updateDashboard();
            }
        } catch (error) {
            console.error('Error loading dashboard data:', error);
        } finally {
            this.hideLoading();
        }
    }
    
    updateDashboard() {
        if (!this.data) return;
        
        this.updateOverviewCards();
        this.updateChart();
        this.updateTransactionsList();
    }
    
    updateOverviewCards() {
        const { financial_summary } = this.data;
        
        // Update cards
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
        
        if (this.chart) {
            this.chart.destroy();
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
                scales: {
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
                    },
                    tooltip: {
                        callbacks: {
                            label: (context) => {
                                return `${context.dataset.label}: ${this.formatCurrency(context.parsed.y)}`;
                            }
                        }
                    }
                }
            }
        });
    }
    
    updateTransactionsList() {
        const { recent_transactions } = this.data;
        const container = document.getElementById('recent-transactions-list');
        
        if (!container) return;
        
        if (recent_transactions.length === 0) {
            container.innerHTML = `
                <div class="text-center py-4 text-muted">
                    <i class="bi bi-inbox fs-1"></i>
                    <p class="mt-2">No recent transactions</p>
                </div>
            `;
            return;
        }
        
        container.innerHTML = recent_transactions.map(transaction => `
            <div class="transaction-item">
                <div class="transaction-icon ${transaction.transaction_type}">
                    <i class="bi ${transaction.transaction_type === 'income' ? 'bi-arrow-down-left' : 'bi-arrow-up-right'}"></i>
                </div>
                <div class="transaction-details">
                    <div class="transaction-description">${transaction.description}</div>
                    <div class="transaction-meta">
                        ${transaction.category} • ${new Date(transaction.date).toLocaleDateString()}
                    </div>
                </div>
                <div class="transaction-amount ${transaction.transaction_type}">
                    ${transaction.transaction_type === 'income' ? '+' : '-'}${this.formatCurrency(Math.abs(transaction.amount))}
                </div>
            </div>
        `).join('');
    }
    
    setupEventListeners() {
        // Refresh button
        const refreshBtn = document.getElementById('refresh-dashboard');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => this.loadDashboardData());
        }
    }
    
    updateElement(id, value) {
        const element = document.getElementById(id);
        if (element) {
            element.textContent = value;
        }
    }
    
    formatCurrency(amount) {
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: 'CAD'
        }).format(amount);
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
}

// Initialize dashboard
window.addEventListener('DOMContentLoaded', () => {
    window.dashboard = new BootstrapDashboard();
});