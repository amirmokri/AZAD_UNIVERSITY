"""
Custom template filters for admin interface.
"""
from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """
    Get item from dictionary using a key.
    Used for accessing schedule_matrix in chart template.
    """
    return dictionary.get(key)
