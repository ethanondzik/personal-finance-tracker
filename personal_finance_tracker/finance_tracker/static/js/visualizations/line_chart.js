document.addEventListener('DOMContentLoaded', function() {
    const dailyDataElement = document.getElementById('daily-data');
    const container = document.getElementById('line-chart');

    if (!dailyDataElement || !container) {
        console.error('Daily data or container element not found.');
        return;
    }

    const dailyData = JSON.parse(dailyDataElement.textContent || '[]');

    if (dailyData.length === 0) {
        container.innerHTML = '<p class="text-center text-muted">No data available for chart</p>';
        return;
    }

    const ctx = container.getContext('2d');

    new Chart(ctx, {
        type: 'line',
        data: {
            labels: dailyData.map(data => data.formatted_date),
            datasets: [{
                label: 'Income',
                data: dailyData.map(data => data.income),
                borderColor: '#4CAF50',
                backgroundColor: function(context) {
                    const chart = context.chart;
                    const {ctx, chartArea} = chart;
                    if (!chartArea) return null;
                    
                    const gradient = ctx.createLinearGradient(0, chartArea.bottom, 0, chartArea.top);
                    gradient.addColorStop(0, 'rgba(76, 175, 80, 0.1)');
                    gradient.addColorStop(1, 'rgba(76, 175, 80, 0.4)');
                    return gradient;
                },
                borderWidth: 3,
                fill: true,
                tension: 0.4,
                pointBackgroundColor: '#4CAF50',
                pointBorderColor: '#ffffff',
                pointBorderWidth: 2,
                pointRadius: 5,
                pointHoverRadius: 8,
            }, {
                label: 'Expenses',
                data: dailyData.map(data => data.expenses),
                borderColor: '#F44336',
                backgroundColor: function(context) {
                    const chart = context.chart;
                    const {ctx, chartArea} = chart;
                    if (!chartArea) return null;
                    
                    const gradient = ctx.createLinearGradient(0, chartArea.bottom, 0, chartArea.top);
                    gradient.addColorStop(0, 'rgba(244, 67, 54, 0.1)');
                    gradient.addColorStop(1, 'rgba(244, 67, 54, 0.4)');
                    return gradient;
                },
                borderWidth: 3,
                fill: true,
                tension: 0.4,
                pointBackgroundColor: '#F44336',
                pointBorderColor: '#ffffff',
                pointBorderWidth: 2,
                pointRadius: 5,
                pointHoverRadius: 8,
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
                        text: 'Date',
                        font: {
                            size: 14,
                            weight: 'bold'
                        }
                    },
                    grid: {
                        display: false
                    },
                    ticks: {
                        maxTicksLimit: 10
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
                            const dayData = dailyData[tooltipItems[0].dataIndex];
                            return [
                                `Net: ${new Intl.NumberFormat('en-CA', {
                                    style: 'currency',
                                    currency: 'CAD'
                                }).format(dayData.net)}`,
                                `Date: ${dayData.date}`
                            ];
                        }
                    }
                }
            },
            animation: {
                duration: 1500,
                easing: 'easeInOutQuart'
            }
        }
    });
});