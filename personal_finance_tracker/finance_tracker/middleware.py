class ThemeMiddleware:
    """
    Middleware to determine user theme preference before template rendering.
    
    This ensures the theme is applied to HTML/body classes during initial page render,
    eliminating the flash of unstyled/wrong-theme content.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Check for theme in cookies first (most current)
        theme = request.COOKIES.get('theme')
        print(f"Theme from cookie: {theme}")  # Debug log

        
        # If no cookie found, default to 'light'
        if not theme:
            theme = 'light'
        
        # Add theme to request object for access in templates
        request.theme = theme
        
        # Continue processing the request
        response = self.get_response(request)
        return response