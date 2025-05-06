(function($) {
  'use strict';
  
  $(function() {
    // Apply theme on initial page load to prevent flashing
    const currentTheme = $('body').hasClass('dark-theme') ? 'dark' : 'light';
    applyTheme(currentTheme);
    
    // Theme toggle click handler
    $('#theme-toggle').on('click', function() {
      const newTheme = $('body').hasClass('dark-theme') ? 'light' : 'dark';
      applyTheme(newTheme);

      // Save theme preferences to DB
      saveThemePreference(newTheme);
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

    // Helper function to save theme preference to user account
    function saveThemePreference(theme) {
      $.ajax({
        url: '/update-theme-preference/',
        type: 'POST',
        data: {
          'theme_preference': true,
          'theme': theme,
          'csrfmiddlewaretoken': document.querySelector('[name=csrfmiddlewaretoken]').value
        },
        success: function(response) {
          console.log('Theme preference saved');
        },
        error: function(xhr, status, error) {
          console.error('Error saving theme preference');
        }
      });
    }
  });
})(jQuery);