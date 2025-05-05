(function($) {
  'use strict';
  
  $(function() {
    console.log('Theme toggle script loaded');

    // First check cookies (server preference)
    const cookieTheme = getCookie('theme');
    console.log('Cookie theme detected:', cookieTheme);

    // Then check localStorage (fallback)
    const storedTheme = localStorage.getItem('theme');
    console.log('LocalStorage theme detected:', storedTheme);

    // Use cookie first, then localStorage, then default to light
    const currentTheme = cookieTheme || storedTheme || 'light';
    console.log('Using theme:', currentTheme);
    
    // IMPORTANT: Apply the theme immediately when page loads
    applyTheme(currentTheme);
    
    // Theme toggle click handler
    $('#theme-toggle').on('click', function() {
      console.log('Theme toggle clicked');
      const newTheme = $('body').hasClass('dark-theme') ? 'light' : 'dark';
      console.log('Switching to theme:', newTheme);
      
      applyTheme(newTheme);
      
      // Save to localStorage for client-side persistence
      localStorage.setItem('theme', newTheme);
      console.log('Theme saved to localStorage');
      
      // Save to cookies for server-side rendering
      setCookie('theme', newTheme, 365);
      console.log('Theme saved to cookie for 365 days');
    });
    
    // Function to apply theme
    function applyTheme(theme) {
      // Remove both theme classes from html and body
      $('html, body').removeClass('light-theme dark-theme');
      
      if (theme === 'dark') {
        // Add dark theme to both html and body
        $('html, body').addClass('dark-theme');
        $('.navbar').addClass('navbar-dark');
        
        // Update icon
        $('#theme-toggle i').removeClass('mdi-brightness-6').addClass('mdi-white-balance-sunny');
      } else {
        // Add light theme to both html and body
        $('html, body').addClass('light-theme');
        $('.navbar').removeClass('navbar-dark');
        
        // Update icon
        $('#theme-toggle i').removeClass('mdi-white-balance-sunny').addClass('mdi-brightness-6');
      }
    }
    
    // Helper function to set cookies with proper attributes
    function setCookie(name, value, days) {
      let expires = '';
      if (days) {
        const date = new Date();
        date.setTime(date.getTime() + (days * 24 * 60 * 60 * 1000));
        expires = '; expires=' + date.toUTCString();
      }
      // Set more cookie attributes to ensure browser compatibility
      document.cookie = name + '=' + value + expires + '; path=/; SameSite=Lax';
      
      // Verify the cookie was set by immediately trying to read it
      const verifySet = getCookie(name);
      console.log('Verified cookie set:', name, '=', verifySet);
    }
    
    // Helper function to get cookie values
    function getCookie(name) {
      const nameEQ = name + '=';
      const ca = document.cookie.split(';');
      for(let i=0; i < ca.length; i++) {
        let c = ca[i];
        while (c.charAt(0) === ' ') c = c.substring(1, c.length);
        if (c.indexOf(nameEQ) === 0) return c.substring(nameEQ.length, c.length);
      }
      return null;
    }
  });
})(jQuery);