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
  });