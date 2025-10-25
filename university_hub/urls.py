"""
URL Configuration for university_hub project.

This module defines the main URL routing for the entire project.
It includes:
- Admin panel URLs
- App-specific URLs (classes app)
- API endpoints
- Static and media file serving in development

URL Structure:
- /admin/ - Django admin panel
- / - Main website URLs (home, class affairs, etc.)
- /api/ - REST API endpoints
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from classes.views import error_404

# Customize admin site headers and titles
admin.site.site_header = settings.ADMIN_SITE_HEADER
admin.site.site_title = settings.ADMIN_SITE_TITLE
admin.site.index_title = settings.ADMIN_INDEX_TITLE

urlpatterns = [
    # Admin panel URL
    path('admin/', admin.site.urls),
    
    # Main application URLs
    path('', include('classes.urls')),
    
    # API URLs for REST Framework
    path('api/', include('classes.api_urls')),
]

# Serve media files in development
# In production, use a proper web server (nginx, Apache) to serve media files
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Custom error handlers
handler404 = error_404

