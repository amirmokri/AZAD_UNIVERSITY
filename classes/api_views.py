"""
API views using Django REST Framework.

This module provides RESTful API endpoints for:
- Listing and retrieving teachers
- Listing and retrieving courses
- Listing and retrieving floors
- Listing and retrieving rooms
- Listing and retrieving class schedules
- Filtering schedules by day and time

All views are read-only for public access.
"""

from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from .models import Faculty, Teacher, Course, Floor, Room, ClassSchedule
from .serializers import (
    FacultySerializer, TeacherSerializer, CourseSerializer, FloorSerializer,
    RoomSerializer, ClassScheduleSerializer
)


class FacultyViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for faculties.
    Supports listing and retrieving faculty information.
    """
    queryset = Faculty.objects.filter(is_active=True)
    serializer_class = FacultySerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['faculty_code', 'faculty_name']
    ordering_fields = ['faculty_code', 'faculty_name']
    ordering = ['faculty_code']


class TeacherViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for teachers.
    Supports listing and retrieving teacher information.
    """
    queryset = Teacher.objects.filter(is_active=True).select_related('faculty')
    serializer_class = TeacherSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['faculty']
    search_fields = ['full_name', 'email', 'faculty__faculty_name']
    ordering_fields = ['full_name', 'faculty']
    ordering = ['faculty', 'full_name']


class CourseViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for courses.
    Supports listing and retrieving course information.
    """
    queryset = Course.objects.filter(is_active=True).select_related('faculty')
    serializer_class = CourseSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['faculty']
    search_fields = ['course_code', 'course_name', 'faculty__faculty_name']
    ordering_fields = ['course_code', 'course_name', 'faculty']
    ordering = ['faculty', 'course_code']


class FloorViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for floors.
    Supports listing and retrieving floor information.
    """
    queryset = Floor.objects.filter(is_active=True).select_related('faculty')
    serializer_class = FloorSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['faculty']
    ordering = ['faculty', 'floor_number']


class RoomViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for rooms.
    Supports listing and retrieving room information with floor filtering.
    """
    queryset = Room.objects.filter(is_active=True).select_related('floor', 'faculty')
    serializer_class = RoomSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['floor', 'room_type', 'position', 'faculty']
    search_fields = ['room_number', 'faculty__faculty_name']
    ordering = ['faculty', 'floor__floor_number', 'room_number']


class ClassScheduleViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for class schedules.
    Supports listing and retrieving schedules with multiple filters.
    """
    queryset = ClassSchedule.objects.filter(is_active=True).select_related(
        'teacher', 'course', 'course__faculty', 'room', 'room__floor'
    )
    serializer_class = ClassScheduleSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['day_of_week', 'time_slot', 'teacher', 'course', 'room', 'course__faculty']
    search_fields = ['course__course_name', 'course__faculty__faculty_name', 'teacher__full_name', 'room__room_number']
    ordering = ['course__faculty', 'day_of_week', 'time_slot']
    
    @action(detail=False, methods=['get'])
    def by_day_and_time(self, request):
        """
        Custom endpoint to get schedules filtered by day and time.
        Usage: /api/schedules/by_day_and_time/?day=saturday&time=08:00
        """
        day = request.query_params.get('day')
        time = request.query_params.get('time')
        
        if not day or not time:
            return Response({
                'error': 'روز و زمان الزامی است.',
                'example': '/api/schedules/by_day_and_time/?day=saturday&time=08:00'
            }, status=400)
        
        schedules = self.get_queryset().filter(
            day_of_week=day,
            time_slot=time
        )
        
        serializer = self.get_serializer(schedules, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def by_teacher_and_day(self, request):
        """
        Custom endpoint to get all schedules for a teacher on a specific day.
        Usage: /api/schedules/by_teacher_and_day/?teacher=احمدی&day=saturday
        """
        teacher_name = request.query_params.get('teacher')
        day = request.query_params.get('day')
        
        if not teacher_name or not day:
            return Response({
                'error': 'نام استاد و روز الزامی است.',
                'example': '/api/schedules/by_teacher_and_day/?teacher=احمدی&day=saturday'
            }, status=400)
        
        schedules = self.get_queryset().filter(
            day_of_week=day,
            teacher__full_name__icontains=teacher_name
        ).order_by('time_slot')
        
        if not schedules.exists():
            return Response({
                'message': f'هیچ کلاسی برای استاد "{teacher_name}" در این روز یافت نشد.',
                'results': []
            })
        
        serializer = self.get_serializer(schedules, many=True)
        
        # Group by time slot
        grouped_data = {}
        for item in serializer.data:
            time_slot = item['time_slot']
            if time_slot not in grouped_data:
                grouped_data[time_slot] = []
            grouped_data[time_slot].append(item)
        
        return Response({
            'teacher': teacher_name,
            'day': day,
            'total_classes': schedules.count(),
            'time_slots': grouped_data,
            'results': serializer.data
        })
