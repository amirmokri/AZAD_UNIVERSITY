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
    # Be defensive: templates may pass None or non-dict objects.
    if dictionary is None:
        return None

    # If object provides mapping-like 'get', use it safely
    if hasattr(dictionary, "get"):
        try:
            return dictionary.get(key)
        except Exception:
            return None

    # Support list/tuple index access when key is int or str int
    try:
        index = int(key) if isinstance(key, str) and key.isdigit() else key
        if isinstance(dictionary, (list, tuple)) and isinstance(index, int):
            return dictionary[index] if 0 <= index < len(dictionary) else None
    except Exception:
        return None

    # Fallback to item access for other mapping-like objects
    try:
        return dictionary[key]
    except Exception:
        return None
