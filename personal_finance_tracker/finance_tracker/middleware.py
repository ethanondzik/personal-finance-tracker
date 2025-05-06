class ThemeMiddleware:
    """
    Middleware to determine user theme preference before template rendering.
    
    This ensures the theme is applied to HTML/body classes during initial page render,
    eliminating the flash of unstyled/wrong-theme content.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # First check for users saved theme preferences in the database
        if request.user.is_authenticated:
            theme = request.user.theme
        else:
            # If user is not authenticated, check for a theme in cookies
            theme = request.COOKIES.get('theme')

            # If no theme cookie is found, default to light theme
            if not theme:
                theme = 'light'

        # Add theme to request object for use in templates
        request.theme = theme

        # Add navbar-specific classes based on theme (to override navbar styling complexities within star admin 2)
        if theme == 'dark':
            request.navbar_class = 'navbar-dark'
        else:
            request.navbar_class = 'navbar-light'


        response = self.get_response(request)
        return response