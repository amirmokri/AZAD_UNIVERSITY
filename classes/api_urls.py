"""
API URL patterns using Django REST Framework routers.

This module defines RESTful API routes for:
- Teachers
- Courses
- Floors
- Rooms
- Class schedules
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api_views import (
    FacultyViewSet, TeacherViewSet, CourseViewSet, FloorViewSet,
    RoomViewSet, ClassScheduleViewSet
)

# Create router and register viewsets
router = DefaultRouter()
router.register(r'faculties', FacultyViewSet, basename='faculty')
router.register(r'teachers', TeacherViewSet, basename='teacher')
router.register(r'courses', CourseViewSet, basename='course')
router.register(r'floors', FloorViewSet, basename='floor')
router.register(r'rooms', RoomViewSet, basename='room')
router.register(r'schedules', ClassScheduleViewSet, basename='schedule')

# API URLs
urlpatterns = [
    path('', include(router.urls)),
]

