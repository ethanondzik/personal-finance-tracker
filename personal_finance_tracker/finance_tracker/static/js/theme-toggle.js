(function($) {
  'use strict';
  
  $(function() {
    // Check for saved theme preference or set default
    const currentTheme = localStorage.getItem('theme') || 'light';
    
    // Apply saved theme on page load
    applyTheme(currentTheme);
    
    // Theme toggle click handler
    $('#theme-toggle').on('click', function() {
      const currentTheme = $('body').hasClass('dark-theme') ? 'light' : 'dark';
      applyTheme(currentTheme);
      localStorage.setItem('theme', currentTheme);
    });
    
    // Function to apply theme
    function applyTheme(theme) {
      const body = $('body');
      
      if (theme === 'dark') {
        body.addClass('dark-theme');
        $('.navbar').addClass('navbar-dark');
        
        // Update icon
        $('#theme-toggle i').removeClass('mdi-brightness-6').addClass('mdi-white-balance-sunny');
        
        // Force refresh transaction list visibility (if it exists)
        setTimeout(function() {
          $('.collapse.show').css('display', '').css('display', 'table-row');
          $('.table-responsive').css('display', '').css('display', 'block');
        }, 100);
        
      } else {
        body.removeClass('dark-theme');
        $('.navbar').removeClass('navbar-dark');
        
        // Update icon
        $('#theme-toggle i').removeClass('mdi-white-balance-sunny').addClass('mdi-brightness-6');
      }
    }
  });
})(jQuery);