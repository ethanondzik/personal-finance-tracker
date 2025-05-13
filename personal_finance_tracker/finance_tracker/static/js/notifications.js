/**
 * Notification Manager for Personal Finance Tracker
 * Handles browser notifications and user preference management
 */
(function() {
    'use strict';
    
    // Notification manager object
    const NotificationManager = {
      // Check if the browser supports notifications
      isSupported: function() {
        return 'Notification' in window;
      },
      
      // Request permission for notifications
      requestPermission: function(callback) {
        if (!this.isSupported()) {
          console.log('This browser does not support notifications');
          return;
        }
        
        Notification.requestPermission().then(function(permission) {
          // Store permission in localStorage
          localStorage.setItem('notification_permission', permission);
          if (callback) callback(permission === 'granted');
        });
      },
      
      // Show a notification
      show: function(title, options = {}) {
        if (!this.isSupported()) return false;
        
        if (Notification.permission !== 'granted') {
          this.requestPermission(function(granted) {
            if (granted) {
              NotificationManager.createNotification(title, options);
            }
          });
        } else {
          return this.createNotification(title, options);
        }
      },
      
      // Create notification helper
      createNotification: function(title, options = {}) {
        // Set default icon if not provided
        if (!options.icon) {
          options.icon = '/static/images/favicon.png';
        }
        
        // Default notification options
        const defaultOptions = {
          body: '',
          silent: false,
          requireInteraction: false
        };
        
        const notificationOptions = {...defaultOptions, ...options};
        
        // Create and return the notification
        const notification = new Notification(title, notificationOptions);
        
        // Handle notification click
        notification.onclick = function(event) {
          event.preventDefault();
          window.focus();
          if (options.onclick) options.onclick(event);
          notification.close();
        };
        
        return notification;
      },
      
      // Get user notification preferences from localStorage
      getUserPreferences: function() {
        const prefsJson = localStorage.getItem('notification_preferences') || '{}';
        try {
          return JSON.parse(prefsJson);
        } catch (e) {
          console.error('Error parsing notification preferences:', e);
          return {};
        }
      },
      
      // Save user notification preferences to localStorage
      saveUserPreferences: function(preferences) {
        localStorage.setItem('notification_preferences', JSON.stringify(preferences));
      },
      
      // Enable/disable specific notification type
      setNotificationPreference: function(type, enabled) {
        const prefs = this.getUserPreferences();
        prefs[type] = enabled;
        this.saveUserPreferences(prefs);
      },
      
      // Check if a specific notification type is enabled
      isNotificationEnabled: function(type) {
        const prefs = this.getUserPreferences();
        // Default to true if not specified
        return prefs[type] !== undefined ? prefs[type] : true;
      }
    };
    
    // Add to global window object
    window.NotificationManager = NotificationManager;
    
    // Initialize when page loads
    document.addEventListener('DOMContentLoaded', function() {
      // Check for existing permission
      if (NotificationManager.isSupported()) {
        const savedPermission = localStorage.getItem('notification_permission');
        
        // If permission was previously granted but browser shows different, update localStorage
        if (savedPermission !== Notification.permission) {
          localStorage.setItem('notification_permission', Notification.permission);
        }
      }
    });
  })();