"""
Search utilities for Elasticsearch.

This module provides search functions for:
- Courses: Search by name, code, description
- Teachers: Search by name, email, specialization
- Combined: Multi-field search across different models

Uses Elasticsearch for fast and flexible search with Persian language support.
"""

from elasticsearch_dsl import Q
from .documents import CourseDocument, TeacherDocument


def search_courses(query, faculty_id=None):
    """
    Search courses by query string.
    
    Args:
        query: Search query string
        faculty_id: Optional faculty ID to filter results
        
    Returns:
        Elasticsearch search object with results
    """
    if not query:
        search = CourseDocument.search()
    else:
        # Create multi-field search query
        q = Q('multi_match', 
              query=query,
              fields=['course_name^3', 'course_code^2', 'description'],
              fuzziness='AUTO')
        search = CourseDocument.search().query(q)
    
    # Filter by faculty if provided
    if faculty_id:
        search = search.filter('term', faculty__id=faculty_id)
    
    # Filter only active courses
    search = search.filter('term', is_active=True)
    
    return search


def search_teachers(query):
    """
    Search teachers by query string.
    
    Args:
        query: Search query string
        
    Returns:
        Elasticsearch search object with results
    """
    if not query:
        search = TeacherDocument.search()
    else:
        # Create multi-field search query
        q = Q('multi_match',
              query=query,
              fields=['full_name^3', 'specialization^2', 'email'],
              fuzziness='AUTO')
        search = TeacherDocument.search().query(q)
    
    # Filter only active teachers
    search = search.filter('term', is_active=True)
    
    return search


def search_all(query, faculty_id=None):
    """
    Search across all models (courses and teachers).
    
    Args:
        query: Search query string
        faculty_id: Optional faculty ID to filter course results
        
    Returns:
        Dictionary with course and teacher results
    """
    course_results = search_courses(query, faculty_id)[:10]  # Top 10 courses
    teacher_results = search_teachers(query)[:10]  # Top 10 teachers
    
    return {
        'courses': course_results,
        'teachers': teacher_results,
    }


def autocomplete_courses(query, faculty_id=None, limit=5):
    """
    Get autocomplete suggestions for courses.
    
    Args:
        query: Partial search query
        faculty_id: Optional faculty ID to filter results
        limit: Maximum number of suggestions
        
    Returns:
        List of course suggestions
    """
    if not query or len(query) < 2:
        return []
    
    # Use prefix query for autocomplete
    q = Q('multi_match',
          query=query,
          fields=['course_name', 'course_code'],
          type='phrase_prefix')
    
    search = CourseDocument.search().query(q)
    
    # Filter by faculty if provided
    if faculty_id:
        search = search.filter('term', faculty__id=faculty_id)
    
    # Filter only active courses
    search = search.filter('term', is_active=True)
    
    # Get top N results
    results = search[:limit]
    
    return [
        {
            'id': hit.id,
            'course_code': hit.course_code,
            'course_name': hit.course_name,
        }
        for hit in results
    ]


def autocomplete_teachers(query, limit=5):
    """
    Get autocomplete suggestions for teachers.
    
    Args:
        query: Partial search query
        limit: Maximum number of suggestions
        
    Returns:
        List of teacher suggestions
    """
    if not query or len(query) < 2:
        return []
    
    # Use prefix query for autocomplete
    q = Q('multi_match',
          query=query,
          fields=['full_name'],
          type='phrase_prefix')
    
    search = TeacherDocument.search().query(q)
    
    # Filter only active teachers
    search = search.filter('term', is_active=True)
    
    # Get top N results
    results = search[:limit]
    
    return [
        {
            'id': hit.id,
            'full_name': hit.full_name,
            'specialization': hit.specialization if hasattr(hit, 'specialization') else None,
        }
        for hit in results
    ]

