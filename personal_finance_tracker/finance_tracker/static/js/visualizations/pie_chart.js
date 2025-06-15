document.addEventListener('DOMContentLoaded', function() {
    const overviewDataElement = document.getElementById('overview-data');
    const incomeCategoriesElement = document.getElementById('income-categories-data');
    const expenseCategoriesElement = document.getElementById('expense-categories-data');

    if (!overviewDataElement) {
        console.error('Overview data element not found.');
        return;
    }

    const overviewData = JSON.parse(overviewDataElement.textContent || '{}');
    const incomeCategories = JSON.parse(incomeCategoriesElement?.textContent || '[]');
    const expenseCategories = JSON.parse(expenseCategoriesElement?.textContent || '[]');

    // Main Overview Pie Chart
    const overviewCtx = document.getElementById('overview-pie-chart');
    if (overviewCtx) {
        new Chart(overviewCtx, {
            type: 'pie',
            data: {
                labels: ['Income', 'Expenses'],
                datasets: [{
                    data: [overviewData.total_income, overviewData.total_expenses],
                    backgroundColor: ['#4CAF50', '#F44336'],
                    borderColor: ['#ffffff', '#ffffff'],
                    borderWidth: 3,
                    hoverBorderWidth: 5
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            usePointStyle: true,
                            pointStyle: 'circle',
                            font: {
                                size: 14,
                                weight: '500'
                            },
                            padding: 20
                        }
                    },
                    tooltip: {
                        backgroundColor: 'rgba(0, 0, 0, 0.8)',
                        titleColor: 'white',
                        bodyColor: 'white',
                        borderColor: 'rgba(255, 255, 255, 0.2)',
                        borderWidth: 1,
                        cornerRadius: 8,
                        callbacks: {
                            label: function(context) {
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const value = context.parsed;
                                const percentage = ((value / total) * 100).toFixed(1);
                                return `${context.label}: ${new Intl.NumberFormat('en-CA', {
                                    style: 'currency',
                                    currency: 'CAD'
                                }).format(value)} (${percentage}%)`;
                            }
                        }
                    }
                },
                animation: {
                    animateRotate: true,
                    duration: 1500
                }
            }
        });
    }

    // Income Categories Pie Chart
    const incomeCtx = document.getElementById('income-pie-chart');
    if (incomeCtx && incomeCategories.length > 0) {
        const incomeColors = [
            '#4CAF50', '#8BC34A', '#CDDC39', '#FFEB3B', '#FFC107',
            '#FF9800', '#FF5722', '#9C27B0', '#673AB7', '#3F51B5'
        ];

        new Chart(incomeCtx, {
            type: 'doughnut',
            data: {
                labels: incomeCategories.map(cat => cat.name),
                datasets: [{
                    data: incomeCategories.map(cat => cat.amount),
                    backgroundColor: incomeColors.slice(0, incomeCategories.length),
                    borderColor: '#ffffff',
                    borderWidth: 2,
                    hoverBorderWidth: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: '60%',
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            usePointStyle: true,
                            pointStyle: 'circle',
                            font: {
                                size: 12
                            },
                            padding: 15
                        }
                    },
                    tooltip: {
                        backgroundColor: 'rgba(0, 0, 0, 0.8)',
                        titleColor: 'white',
                        bodyColor: 'white',
                        borderColor: 'rgba(255, 255, 255, 0.2)',
                        borderWidth: 1,
                        cornerRadius: 8,
                        callbacks: {
                            label: function(context) {
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const value = context.parsed;
                                const percentage = ((value / total) * 100).toFixed(1);
                                return `${context.label}: ${new Intl.NumberFormat('en-CA', {
                                    style: 'currency',
                                    currency: 'CAD'
                                }).format(value)} (${percentage}%)`;
                            }
                        }
                    }
                },
                animation: {
                    animateRotate: true,
                    duration: 1500
                }
            }
        });
    }

    // Expense Categories Pie Chart
    const expenseCtx = document.getElementById('expense-pie-chart');
    if (expenseCtx && expenseCategories.length > 0) {
        const expenseColors = [
            '#F44336', '#E91E63', '#9C27B0', '#673AB7', '#3F51B5',
            '#2196F3', '#03A9F4', '#00BCD4', '#009688', '#4CAF50'
        ];

        new Chart(expenseCtx, {
            type: 'doughnut',
            data: {
                labels: expenseCategories.map(cat => cat.name),
                datasets: [{
                    data: expenseCategories.map(cat => cat.amount),
                    backgroundColor: expenseColors.slice(0, expenseCategories.length),
                    borderColor: '#ffffff',
                    borderWidth: 2,
                    hoverBorderWidth: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: '60%',
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            usePointStyle: true,
                            pointStyle: 'circle',
                            font: {
                                size: 12
                            },
                            padding: 15
                        }
                    },
                    tooltip: {
                        backgroundColor: 'rgba(0, 0, 0, 0.8)',
                        titleColor: 'white',
                        bodyColor: 'white',
                        borderColor: 'rgba(255, 255, 255, 0.2)',
                        borderWidth: 1,
                        cornerRadius: 8,
                        callbacks: {
                            label: function(context) {
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const value = context.parsed;
                                const percentage = ((value / total) * 100).toFixed(1);
                                return `${context.label}: ${new Intl.NumberFormat('en-CA', {
                                    style: 'currency',
                                    currency: 'CAD'
                                }).format(value)} (${percentage}%)`;
                            }
                        }
                    }
                },
                animation: {
                    animateRotate: true,
                    duration: 1500
                }
            }
        });
    }
});