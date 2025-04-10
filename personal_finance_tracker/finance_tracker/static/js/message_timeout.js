// This script will remove any alert messages after 10 seconds

document.addEventListener('DOMContentLoaded', function () {
    // Select all alert elements
    const alerts = document.querySelectorAll('.alert');

    // Set a timeout to remove each alert after 10 seconds
    alerts.forEach(alert => {
      setTimeout(() => {
        alert.classList.remove('show'); // Bootstrap's fade-out class
        alert.addEventListener('transitionend', () => alert.remove()); // Remove from DOM after fade-out
      }, 10000); 
    });
  });