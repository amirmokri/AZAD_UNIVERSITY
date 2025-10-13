"""
App configuration for the classes application.

This app handles all class scheduling, room management, and teacher assignments.
"""

from django.apps import AppConfig


class ClassesConfig(AppConfig):
    """Configuration class for the classes app"""
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'classes'
    verbose_name = 'مدیریت کلاس‌ها'  # Persian name for admin panel
