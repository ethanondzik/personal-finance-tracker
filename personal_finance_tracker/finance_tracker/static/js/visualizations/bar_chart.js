document.addEventListener('DOMContentLoaded', function() {
    const monthlyDataElement = document.getElementById('monthly-data');
    const container = document.getElementById('bar-chart');

    if (!monthlyDataElement || !container) {
        console.error('Monthly data or container element not found.');
        return;
    }

    const monthlyData = JSON.parse(monthlyDataElement.textContent || '[]');

    if (monthlyData.length === 0) {
        container.innerHTML = '<p class="text-center text-muted">No data available for chart</p>';
        return;
    }

    const ctx = container.getContext('2d');

    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: monthlyData.map(data => data.month),
            datasets: [{
                label: 'Income',
                data: monthlyData.map(data => data.income),
                backgroundColor: '#4CAF50',
                borderColor: '#4CAF50',
                borderWidth: 1,
                borderRadius: 8,
                borderSkipped: false,
            }, {
                label: 'Expenses',
                data: monthlyData.map(data => data.expenses),
                backgroundColor: '#F44336',
                borderColor: '#F44336',
                borderWidth: 1,
                borderRadius: 8,
                borderSkipped: false,
            }, {
                label: 'Net',
                data: monthlyData.map(data => data.net),
                backgroundColor: monthlyData.map(data => data.net >= 0 ? '#2196F3' : '#FF9800'),
                borderColor: monthlyData.map(data => data.net >= 0 ? '#2196F3' : '#FF9800'),
                borderWidth: 1,
                borderRadius: 8,
                borderSkipped: false,
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
                    title: {
                        display: true,
                        text: 'Month',
                        font: {
                            size: 14,
                            weight: 'bold'
                        }
                    },
                    grid: {
                        display: false
                    }
                },
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Amount (CAD)',
                        font: {
                            size: 14,
                            weight: 'bold'
                        }
                    },
                    grid: {
                        color: 'rgba(0, 0, 0, 0.1)'
                    }
                }
            },
            plugins: {
                legend: {
                    position: 'top',
                    labels: {
                        usePointStyle: true,
                        pointStyle: 'circle',
                        font: {
                            size: 12,
                            weight: '500'
                        }
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
                            let label = context.dataset.label || '';
                            if (label) {
                                label += ': ';
                            }
                            if (context.parsed.y !== null) {
                                label += new Intl.NumberFormat('en-CA', {
                                    style: 'currency',
                                    currency: 'CAD'
                                }).format(context.parsed.y);
                            }
                            return label;
                        },
                        afterBody: function(tooltipItems) {
                            const monthData = monthlyData[tooltipItems[0].dataIndex];
                            return `Net: ${new Intl.NumberFormat('en-CA', {
                                style: 'currency',
                                currency: 'CAD'
                            }).format(monthData.net)}`;
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
});