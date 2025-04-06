// Yagna's Code that was refactored to be able to be a external js file
document.addEventListener('DOMContentLoaded', function() {
  // Geting chart data from template
  const chartData = JSON.parse(document.getElementById('chart-data').textContent);
  
  // Initialize Line Chart
  const lineChartEl = document.getElementById('transactionChart');
  if (lineChartEl) {
    const chart = new Chart(lineChartEl, {
      type: 'line',
      data: {
          labels: chartData.dates,
          datasets: [
              {
                  label: 'Income',
                  data: chartData.income,
                  borderColor: '#4CAF50',
                  backgroundColor: (context) => {
                      const chart = context.chart;
                      const {ctx, chartArea} = chart;
                      if (!chartArea) return null;
                      
                      const gradient = ctx.createLinearGradient(
                          0, chartArea.bottom, 
                          0, chartArea.top
                      );
                      gradient.addColorStop(0, 'rgba(76, 175, 80, 0)');
                      gradient.addColorStop(1, 'rgba(76, 175, 80, 0.3)');
                      return gradient;
                  },
                  tension: 0.2,
                  fill: true
              },
              {
                  label: 'Expenses',
                  data: chartData.expenses,
                  borderColor: '#F44336',
                  backgroundColor: (context) => {
                      const chart = context.chart;
                      const {ctx, chartArea} = chart;
                      if (!chartArea) return null;
                      
                      const gradient = ctx.createLinearGradient(
                          0, chartArea.bottom, 
                          0, chartArea.top
                      );
                      gradient.addColorStop(0, 'rgba(244, 67, 54, 0)');
                      gradient.addColorStop(1, 'rgba(244, 67, 54, 0.3)');
                      return gradient;
                  },
                  tension: 0.2,
                  fill: true
              }
          ]
      },
      options: {
          responsive: true,
          maintainAspectRatio: false,
          scales: {
            y: {
              beginAtZero: true,
              title: { display: true, text: 'Amount (CAD)' },
            },
            x: {
              title: { display: true, text: 'Date' },
              ticks: { autoSkip: true, maxTicksLimit: 10 },
              grid: { display: false }
            },
          },
          plugins: {
            legend: {
                labels: {
                    usePointStyle: true,
                    pointStyle: 'circle'
                }
            }
          }
      },
    });
  }

  // Initialize Pie Chart
  const pieChartEl = document.getElementById('pieChart');
  if (pieChartEl) {
      new Chart(pieChartEl, {
        type: 'pie',
        data: {
          labels: ['Income', 'Expenses'],
          datasets: [{
            data: [chartData.total_income, chartData.total_expenses],
            backgroundColor: ['#36A2EB', '#FF6384'],
            borderWidth: 1
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: true,
          plugins: {
            legend: { 
              labels: {
                usePointStyle: true,
                pointStyle: 'circle'
              },
              position: 'bottom'
            },
            tooltip: {
              callbacks: {
                label: (context) => {
                  const total = context.dataset.data.reduce((a, b) => a + b);
                  const value = context.parsed;
                  const percentage = ((value / total) * 100).toFixed(1) + '%';
                  return `${context.label}: $${value.toFixed(2)} (${percentage})`;
                }
              }
            }
          }
        }
      });
  }

  // Initialize Monthly Bar Chart
  const barCtx = document.getElementById('monthlyBarChart');
  if (barCtx) {
    new Chart(barCtx, {
        type: 'bar',
        data: {
            labels: chartData.months,
            datasets: [{
                label: 'Income',
                data: chartData.monthly_income,
                backgroundColor: '#1ABC9C',
                borderColor: '#1ABC9C',
                borderWidth: 1
            }, {
                label: 'Expenses',
                data: chartData.monthly_expenses,
                backgroundColor: '#E67E22',
                borderColor: '#E67E22',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Amount (CAD)'
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: 'Month'
                    },
                    stacked: false
                }
            },
            plugins: {
                legend: {
                    labels: {
                      usePointStyle: true,
                      pointStyle: 'circle'
                    },
                    position: 'top'
                },
                tooltip: {
                    callbacks: {
                        label: (context) => {
                            let label = context.dataset.label || '';
                            if (label) label += ': ';
                            if (context.parsed.y !== null) {
                                label += new Intl.NumberFormat('en-CA', {
                                    style: 'currency',
                                    currency: 'CAD'
                                }).format(context.parsed.y);
                            }
                            return label;
                        }
                    }
                }
            }
        }
    });
  }
});