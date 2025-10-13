"""
URL patterns for the classes app.

This module defines URL routing for:
- Home page
- Faculty selection page
- Class affairs page (day selection)
- Time selection page
- Floor view page

All URLs use descriptive Persian slugs where appropriate.
"""

from django.urls import path
from . import views

app_name = 'classes'

urlpatterns = [
    # Home page
    path('', views.home, name='home'),
    
    # Faculty selection page
    path('select-faculty/', views.faculty_selection, name='faculty_selection'),
    
    # Class affairs page (day selection) with faculty
    path('faculty/<int:faculty_id>/class-affairs/', views.class_affairs, name='class_affairs'),
    
    # Time selection page for a specific faculty and day
    path('faculty/<int:faculty_id>/class-affairs/<str:day>/', views.time_selection, name='time_selection'),
    
    # Floor view for a specific faculty, day and time
    path('faculty/<int:faculty_id>/class-affairs/<str:day>/<str:time>/', views.floor_view, name='floor_view'),
    
    # Teacher classes quick search (for home page search feature)
    path('teacher-classes/<str:day>/', views.teacher_classes_view, name='teacher_classes'),
    
    # Search endpoints
    path('search/', views.search_view, name='search'),
    path('api/search/', views.search_api, name='search_api'),
    path('api/teacher-autocomplete/', views.elasticsearch_teacher_autocomplete, name='teacher_autocomplete'),
    
    # Voting endpoints
    path('api/vote-cancellation/', views.vote_class_cancellation, name='vote_cancellation'),
    path('api/vote-confirmation/', views.vote_class_confirmation, name='vote_confirmation'),
    
    # Error pages
    path('error/', views.error_404, name='error_404'),
]

