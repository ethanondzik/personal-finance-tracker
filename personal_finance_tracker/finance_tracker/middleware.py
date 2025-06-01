class ThemeMiddleware:
    """
    Middleware to determine user theme preference before template rendering.
    
    This ensures the theme is applied to HTML/body classes during initial page render,
    eliminating the flash of unstyled/wrong-theme content.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Only apply theme to pages that authenticated users can access (i.e. all pages except the login and landing page)
        if request.user.is_authenticated:
            theme = request.user.theme

            request.theme = theme
            
            # Add theme to request object for use in templates
            request.theme = theme

            # Add navbar-specific classes based on theme (to override navbar styling complexities within star admin 2)
            if theme == 'dark':
                request.navbar_class = 'navbar-dark'
            else:
                request.navbar_class = 'navbar-light'
        else:
            # Default theme for unauthenticated users
            request.theme = 'light'
            request.navbar_class = 'navbar-light'


        response = self.get_response(request)
        return response