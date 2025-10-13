"""
DRF Serializers for API endpoints.

This module defines serializers for:
- Faculty
- Teacher
- Course
- Floor
- Room
- ClassSchedule

Serializers convert model instances to JSON for API responses.
"""

from rest_framework import serializers
from .models import Faculty, Teacher, Course, Floor, Room, ClassSchedule


class FacultySerializer(serializers.ModelSerializer):
    """Serializer for Faculty model"""
    
    image_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Faculty
        fields = ['id', 'faculty_code', 'faculty_name', 'faculty_image', 'image_url', 'description', 'is_active']
    
    def get_image_url(self, obj):
        """Get the static URL for the faculty image"""
        if obj.faculty_image:
            return f'/static/images/{obj.faculty_image}'
        return None


class TeacherSerializer(serializers.ModelSerializer):
    """Serializer for Teacher model"""
    
    faculty_name = serializers.CharField(source='faculty.faculty_name', read_only=True, allow_null=True)
    
    class Meta:
        model = Teacher
        fields = ['id', 'faculty', 'faculty_name', 'full_name', 'email', 'phone_number', 'specialization', 'is_active']


class CourseSerializer(serializers.ModelSerializer):
    """Serializer for Course model"""
    
    faculty_name = serializers.CharField(source='faculty.faculty_name', read_only=True)
    
    class Meta:
        model = Course
        fields = ['id', 'faculty', 'faculty_name', 'course_code', 'course_name', 'credit_hours', 'description', 'is_active']


class FloorSerializer(serializers.ModelSerializer):
    """Serializer for Floor model"""
    
    faculty_name = serializers.CharField(source='faculty.faculty_name', read_only=True, allow_null=True)
    
    class Meta:
        model = Floor
        fields = ['id', 'faculty', 'faculty_name', 'floor_number', 'floor_name', 'description', 'is_active']


class RoomSerializer(serializers.ModelSerializer):
    """Serializer for Room model with nested floor information"""
    
    floor_name = serializers.CharField(source='floor.floor_name', read_only=True)
    faculty_name = serializers.CharField(source='faculty.faculty_name', read_only=True, allow_null=True)
    room_type_display = serializers.CharField(source='get_room_type_display', read_only=True)
    position_display = serializers.CharField(source='get_position_display', read_only=True)
    
    class Meta:
        model = Room
        fields = [
            'id', 'faculty', 'faculty_name', 'floor', 'floor_name', 'room_number', 'room_type', 
            'room_type_display', 'capacity', 'position', 'position_display', 'is_active'
        ]


class ClassScheduleSerializer(serializers.ModelSerializer):
    """Serializer for ClassSchedule model with all related information"""
    
    teacher_name = serializers.CharField(source='teacher.full_name', read_only=True, allow_null=True)
    course_code = serializers.CharField(source='course.course_code', read_only=True)
    course_name = serializers.CharField(source='course.course_name', read_only=True)
    faculty_name = serializers.CharField(source='course.faculty.faculty_name', read_only=True, allow_null=True)
    room_number = serializers.CharField(source='room.room_number', read_only=True)
    room_capacity = serializers.IntegerField(source='room.capacity', read_only=True)
    floor_name = serializers.CharField(source='room.floor.floor_name', read_only=True)
    day_display = serializers.CharField(source='get_day_of_week_display', read_only=True)
    time_display = serializers.CharField(source='get_time_slot_display', read_only=True)
    
    class Meta:
        model = ClassSchedule
        fields = [
            'id', 'teacher', 'teacher_name', 'course', 'course_code', 'course_name', 'faculty_name',
            'room', 'room_number', 'room_capacity', 'floor_name', 
            'day_of_week', 'day_display', 'time_slot', 'time_display',
            'semester', 'academic_year', 'notes', 'is_holding', 'is_active'
        ]

