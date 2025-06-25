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
            
        else:
            # Default theme for unauthenticated users
            request.theme = 'light'
            


        response = self.get_response(request)
        return response