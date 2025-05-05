(function($) {
  'use strict';
  
  $(function() {
    // Apply theme on initial page load to prevent flashing
    const currentTheme = localStorage.getItem('theme') || 'light';
    applyTheme(currentTheme);
    
    // Theme toggle click handler
    $('#theme-toggle').on('click', function() {
      const newTheme = $('body').hasClass('dark-theme') ? 'light' : 'dark';
      applyTheme(newTheme);
      
      // Save to localStorage for client-side persistence
      localStorage.setItem('theme', newTheme);
      
      // Save to cookies for server-side rendering
      setCookie('theme', newTheme, 365);
    });
    
    // Function to apply theme
    function applyTheme(theme) {
      // Remove all theme classes
      $('html, body').removeClass('light-theme dark-theme');
      
      // Remove navbar specific classes that Star Admin 2 might be applying
      $('.navbar').removeClass('navbar-light navbar-dark navbar-primary navbar-success navbar-info navbar-warning navbar-danger');
      $('.navbar-brand-wrapper').css('background-color', '');
      $('.navbar-menu-wrapper').css('background-color', '');
      
      if (theme === 'dark') {
        // Add dark theme to HTML and body
        $('html, body').addClass('dark-theme');
        
        // Apply dark styling to navbar components
        $('.navbar').addClass('navbar-dark');
        $('.navbar-brand-wrapper').css('background-color', '#2d2d2d');
        $('.navbar-menu-wrapper').css('background-color', '#2d2d2d');
        $('.text-center.navbar-brand-wrapper').css('background-color', '#2d2d2d');
        
        // Update icon
        $('#theme-toggle i').removeClass('mdi-brightness-6').addClass('mdi-white-balance-sunny');
      } else {
        // Add light theme to HTML and body
        $('html, body').addClass('light-theme');
        
        // Clear inline styles and let Star Admin 2's default light styling take over
        $('.navbar-brand-wrapper').css('background-color', '');
        $('.navbar-menu-wrapper').css('background-color', '');
        $('.text-center.navbar-brand-wrapper').css('background-color', '');
        
        // Update icon
        $('#theme-toggle i').removeClass('mdi-white-balance-sunny').addClass('mdi-brightness-6');
      }
    }
    
    // Helper function to set cookies
    function setCookie(name, value, days) {
      let expires = '';
      if (days) {
        const date = new Date();
        date.setTime(date.getTime() + (days * 24 * 60 * 60 * 1000));
        expires = '; expires=' + date.toUTCString();
      }
      document.cookie = name + '=' + value + expires + '; path=/; SameSite=Lax';
    }
  });
})(jQuery);