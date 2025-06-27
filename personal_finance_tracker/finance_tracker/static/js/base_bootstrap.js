// Theme Toggle and Base Template Functionality
document.addEventListener('DOMContentLoaded', function() {
    initializeThemeToggle();
    initializeSidebar();
    initializeNotifications();
});

// Theme Management
function initializeThemeToggle() {
    const themeToggle = document.getElementById('themeToggle');
    const themeIcon = document.getElementById('themeIcon');
    const themeText = document.getElementById('themeText');
    const html = document.documentElement;
    
    // Set initial icon and text based on current theme
    updateThemeUI(html.getAttribute('data-bs-theme'));
    
    if (themeToggle) {
        themeToggle.addEventListener('click', function() {
            const currentTheme = html.getAttribute('data-bs-theme');
            const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
            
            // Apply theme immediately to prevent flash
            html.setAttribute('data-bs-theme', newTheme);
            document.body.className = document.body.className.replace(/\b(light-theme|dark-theme)\b/g, '');
            document.body.classList.add(newTheme + '-theme');
            
            updateThemeUI(newTheme);
            saveThemePreference(newTheme);
        });
    }
    
    function updateThemeUI(theme) {
        if (!themeIcon || !themeText) return;
        
        if (theme === 'dark') {
            themeIcon.className = 'bi bi-moon-fill me-2';
            themeText.textContent = 'Switch to Light Mode';
        } else {
            themeIcon.className = 'bi bi-sun-fill me-2';
            themeText.textContent = 'Switch to Dark Mode';
        }
    }
    
    function saveThemePreference(theme) {
        fetch('/update-theme-preference/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-CSRFToken': getCSRFToken()
            },
            body: 'theme=' + encodeURIComponent(theme)
        })
        .catch(() => {
            console.error('Could not update theme preference');
        });
    }
}

// Sidebar Management
function initializeSidebar() {
    const sidebarToggle = document.getElementById('sidebarToggle');
    const sidebar = document.getElementById('sidebar');
    const sidebarBackdrop = document.getElementById('sidebarBackdrop');
    
    // Mobile sidebar toggle
    if (sidebarToggle) {
        sidebarToggle.addEventListener('click', function() {
            sidebar?.classList.toggle('show');
            sidebarBackdrop?.classList.toggle('show');
        });
    }
    
    // Backdrop click to close
    if (sidebarBackdrop) {
        sidebarBackdrop.addEventListener('click', function() {
            sidebar?.classList.remove('show');
            sidebarBackdrop?.classList.remove('show');
        });
    }
    
    // Desktop sidebar collapse (optional)
    const sidebarCollapseBtn = document.getElementById('sidebarCollapseDesktop');
    if (sidebarCollapseBtn) {
        sidebarCollapseBtn.addEventListener('click', function() {
            document.body.classList.toggle('sidebar-collapsed');
        });
    }
    
    // Close sidebar on escape key
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape' && sidebar?.classList.contains('show')) {
            sidebar.classList.remove('show');
            sidebarBackdrop?.classList.remove('show');
        }
    });
}

// Notification System
function initializeNotifications() {
    // Global notification function
    window.showNotification = function(message, type = 'info', duration = 5000) {
        createToast(message, type, duration);
    };
    
    // Auto-hide Django messages
    const alerts = document.querySelectorAll('.alert[data-bs-dismiss="alert"]');
    alerts.forEach(alert => {
        setTimeout(() => {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert?.close();
        }, 5000);
    });
}

// Utility Functions
function getCSRFToken() {
    const cookieValue = document.cookie
        .split('; ')
        .find(row => row.startsWith('csrftoken='));
    return cookieValue ? cookieValue.split('=')[1] : '';
}

function createToast(message, type = 'info', duration = 5000) {
    // Create toast container if it doesn't exist
    let toastContainer = document.getElementById('toast-container');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.id = 'toast-container';
        toastContainer.className = 'toast-container position-fixed top-0 end-0 p-3';
        toastContainer.style.zIndex = '9999';
        document.body.appendChild(toastContainer);
    }
    
    // Create toast
    const toastId = 'toast-' + Date.now();
    const toastHtml = `
        <div id="${toastId}" class="toast" role="alert" aria-live="assertive" aria-atomic="true">
            <div class="toast-header">
                <i class="bi bi-${getToastIcon(type)} me-2 text-${type}"></i>
                <strong class="me-auto">Notification</strong>
                <button type="button" class="btn-close" data-bs-dismiss="toast"></button>
            </div>
            <div class="toast-body">
                ${message}
            </div>
        </div>
    `;
    
    toastContainer.insertAdjacentHTML('beforeend', toastHtml);
    
    // Show toast
    const toastElement = document.getElementById(toastId);
    const toast = new bootstrap.Toast(toastElement, { delay: duration });
    toast.show();
    
    // Remove from DOM after hiding
    toastElement.addEventListener('hidden.bs.toast', function() {
        toastElement.remove();
    });
}

function getToastIcon(type) {
    const icons = {
        'success': 'check-circle',
        'danger': 'exclamation-triangle',
        'warning': 'exclamation-circle',
        'info': 'info-circle'
    };
    return icons[type] || 'info-circle';
}

// Global loading utility
window.showGlobalLoading = function() {
    const loadingHtml = `
        <div class="loading-overlay" id="global-loading-overlay">
            <div class="text-center">
                <div class="spinner-border text-primary" role="status" style="width: 3rem; height: 3rem;">
                    <span class="visually-hidden">Loading...</span>
                </div>
                <p class="mt-3 text-muted">Please wait...</p>
            </div>
        </div>
    `;
    document.body.insertAdjacentHTML('beforeend', loadingHtml);
};

window.hideGlobalLoading = function() {
    const loadingOverlay = document.getElementById('global-loading-overlay');
    if (loadingOverlay) {
        loadingOverlay.remove();
    }
};