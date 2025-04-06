// Yagna's Code that was refactored to be able to be a external js file
document.addEventListener('DOMContentLoaded', function () {
    const chartEl = document.getElementById('transactionChart');
    if (!chartEl) return;

    const chartData = JSON.parse(document.getElementById('chart-data').textContent);

    const config = {
      type: 'line',
      data: {
        labels: chartData.dates,
        datasets: [
          {
            label: 'Income',
            data: chartData.income,
            borderColor: '#4CAF50',
            backgroundColor: '#4CAF5020',
            tension: 0.2,
          },
          {
            label: 'Expenses',
            data: chartData.expenses,
            borderColor: '#F44336',
            backgroundColor: '#F4433620',
            tension: 0.2,
          },
        ],
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
          },
        },
      },
    };

    const chartTab = document.getElementById('chart-tab');
    chartTab.addEventListener('shown.bs.tab', function () {
      new Chart(chartEl, config);
    });

  const pieChartEl = document.getElementById('pieChart');
  if (pieChartEl) {
    const pieConfig = {
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
        maintainAspectRatio: false,
        plugins: {
          legend: { position: 'bottom' },
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
    };
  
    document.getElementById('pie-tab').addEventListener('shown.bs.tab', () => {
      new Chart(pieChartEl, pieConfig);
    });
  }
});