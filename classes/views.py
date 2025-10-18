"""
Views for the class scheduling system.

This module contains view functions for:
- Home page (hero section)
- Faculty selection page
- Class affairs page (day selection)
- Time selection page
- Floor/room display page

All views include error handling and are optimized for Persian/Farsi content.
"""

from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from datetime import timedelta, time as dtime
import hashlib
from .models import Faculty, ClassSchedule, Floor, Room, Course, Teacher, ClassCancellationVote, ClassConfirmationVote
from .search import search_courses, search_teachers, autocomplete_courses, autocomplete_teachers
from django.db.models import Q
import json


def home(request):
    """
    Home page view with hero section.
    
    Displays the main landing page with full-page hero image
    and welcome text.
    
    Args:
        request: Django HTTP request object
        
    Returns:
        Rendered home.html template
    """
    context = {
        'page_title': 'خانه',
    }
    return render(request, 'classes/home.html', context)


def faculty_selection(request):
    """
    Faculty selection page view.
    
    Displays all available faculties for users to choose from.
    
    Args:
        request: Django HTTP request object
        
    Returns:
        Rendered faculty_selection.html template with faculty list
    """
    
    # Get all active faculties
    faculties = Faculty.objects.filter(is_active=True).order_by('faculty_name')
    
    context = {
        'page_title': 'انتخاب دانشکده',
        'faculties': faculties,
    }
    return render(request, 'classes/faculty_selection.html', context)


def class_affairs(request, faculty_id):
    """
    Class affairs page view.
    
    Displays introduction and day selection buttons for users
    to choose which day they want to view schedules for.
    
    Args:
        request: Django HTTP request object
        faculty_id: Selected faculty ID
        
    Returns:
        Rendered class_affairs.html template with day choices
    """
    
    # Get the selected faculty
    faculty = get_object_or_404(Faculty, id=faculty_id, is_active=True)
    
    # List of days in Persian
    days = [
        {'key': 'saturday', 'name': 'شنبه'},
        {'key': 'sunday', 'name': 'یکشنبه'},
        {'key': 'monday', 'name': 'دوشنبه'},
        {'key': 'tuesday', 'name': 'سه‌شنبه'},
        {'key': 'wednesday', 'name': 'چهارشنبه'},
        {'key': 'thursday', 'name': 'پنجشنبه'},
        {'key': 'friday', 'name': 'جمعه'},
    ]
    
    # Get all available time slots from actual schedules in this faculty
    from classes.models import ClassSchedule
    from django.db.models import Q
    
    # Get distinct start times from schedules in this faculty
    schedules = ClassSchedule.objects.filter(
        Q(room__floor__faculty=faculty) | Q(course__faculty=faculty),
        is_active=True
    ).select_related('room__floor', 'course')
    
    # Group schedules by day and start time
    day_schedules = {}
    for schedule in schedules:
        day = schedule.day_of_week
        if day not in day_schedules:
            day_schedules[day] = {}
        
        # Use start_time as key, group schedules by same start time
        start_key = schedule.start_time.strftime('%H:%M') if schedule.start_time else 'unknown'
        if start_key not in day_schedules[day]:
            day_schedules[day][start_key] = {
                'start_time': schedule.start_time,
                'end_time': schedule.end_time,
                'schedules': [],
                'count': 0
            }
        
        day_schedules[day][start_key]['schedules'].append(schedule)
        day_schedules[day][start_key]['count'] += 1
    
    # Add time info to days
    for day in days:
        day_key = day['key']
        if day_key in day_schedules:
            # Sort time slots by start time
            time_slots = sorted(day_schedules[day_key].items(), 
                              key=lambda x: x[1]['start_time'] or dtime.min)
            day['time_slots'] = []
            for start_key, slot_data in time_slots:
                day['time_slots'].append({
                    'start_time': slot_data['start_time'],
                    'end_time': slot_data['end_time'],
                    'start_display': slot_data['start_time'].strftime('%H:%M') if slot_data['start_time'] else 'نامشخص',
                    'end_display': slot_data['end_time'].strftime('%H:%M') if slot_data['end_time'] else 'نامشخص',
                    'count': slot_data['count'],
                    'schedules': slot_data['schedules']
                })
        else:
            day['time_slots'] = []
    
    context = {
        'page_title': 'امور کلاس‌ها',
        'faculty': faculty,
        'days': days,
    }
    return render(request, 'classes/class_affairs.html', context)


def time_selection(request, faculty_id, day):
    """
    Time selection page view.
    
    After selecting a day, this view displays available time slots
    for that specific day.
    
    Args:
        request: Django HTTP request object
        faculty_id: Selected faculty ID
        day: Selected day of the week (e.g., 'saturday')
        
    Returns:
        Rendered time_selection.html template with time slots
    """
    
    # Get the selected faculty
    faculty = get_object_or_404(Faculty, id=faculty_id, is_active=True)
    
    # Validate day parameter
    valid_days = ['saturday', 'sunday', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday']
    if day not in valid_days:
        # Handle invalid day with error message
        context = {
            'error': 'روز انتخاب شده معتبر نیست.'
        }
        return render(request, 'classes/error.html', context, status=400)
    
    # Day names in Persian
    day_names = {
        'saturday': 'شنبه',
        'sunday': 'یکشنبه',
        'monday': 'دوشنبه',
        'tuesday': 'سه‌شنبه',
        'wednesday': 'چهارشنبه',
        'thursday': 'پنجشنبه',
        'friday': 'جمعه',
    }
    
    # Time slots for courses with 2 or less credit hours
    times_2_or_less = [
        {'key': '07:30-09:15', 'name': '7:30 - 9:15 صبح', 'display': '7:30-9:15'},
        {'key': '09:15-11:00', 'name': '9:15 - 11:00 صبح', 'display': '9:15-11:00'},
        {'key': '11:00-13:15', 'name': '11:00 - 13:15', 'display': '11:00-13:15'},
        {'key': '13:15-15:00', 'name': '13:15 - 15:00 بعدازظهر', 'display': '13:15-15:00'},
        {'key': '15:00-16:45', 'name': '15:00 - 16:45 بعدازظهر', 'display': '15:00-16:45'},
        {'key': '16:45-18:00', 'name': '16:45 - 18:00 عصر', 'display': '16:45-18:00'},
    ]
    
    # Time slots for courses with 3 or more credit hours
    times_3_or_more = [
        {'key': '07:30-10:10', 'name': '7:30 - 10:10 صبح', 'display': '7:30-10:10'},
        {'key': '10:15-13:30', 'name': '10:15 - 13:30', 'display': '10:15-13:30'},
        {'key': '13:30-16:00', 'name': '13:30 - 16:00 بعدازظهر', 'display': '13:30-16:00'},
        {'key': '16:00-18:30', 'name': '16:00 - 18:30 عصر', 'display': '16:00-18:30'},
    ]
    
    context = {
        'page_title': f'انتخاب زمان - {day_names[day]}',
        'faculty': faculty,
        'selected_day': day,
        'day_name': day_names[day],
        'times_2_or_less': times_2_or_less,
        'times_3_or_more': times_3_or_more,
    }
    return render(request, 'classes/time_selection.html', context)


def floor_view(request, faculty_id, day, time):
    """
    Floor and room display view with search functionality.
    
    Displays all floors with their rooms and scheduled classes
    for the selected day and time. Supports searching by teacher name or course name.
    
    This is the main view where students see the visual representation
    of classes across different floors.
    
    Features:
    - Room positioning based on position field (left/right/center)
    - Search functionality for teachers and courses
    - Student voting system for class status
    - Responsive design for mobile and desktop
    
    Args:
        request: Django HTTP request object
        faculty_id: Selected faculty ID
        day: Selected day of the week
        time: Selected time slot
        
    Returns:
        Rendered floor_view.html template with floors and schedules
    """
    
    # Get the selected faculty
    faculty = get_object_or_404(Faculty, id=faculty_id, is_active=True)
    
    # Validate parameters
    valid_days = ['saturday', 'sunday', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday']
    
    if day not in valid_days:
        context = {
            'error': 'روز انتخاب شده معتبر نیست.'
        }
        return render(request, 'classes/error.html', context, status=400)
    
    # Day and time names in Persian
    day_names = {
        'saturday': 'شنبه',
        'sunday': 'یکشنبه',
        'monday': 'دوشنبه',
        'tuesday': 'سه‌شنبه',
        'wednesday': 'چهارشنبه',
        'thursday': 'پنجشنبه',
        'friday': 'جمعه',
    }
    
    # Time names for display
    time_names = {
        '07:30-09:15': '7:30-9:15 صبح',
        '09:15-11:00': '9:15-11:00 صبح',
        '11:00-13:15': '11:00-13:15',
        '13:15-15:00': '13:15-15:00 بعدازظهر',
        '15:00-16:45': '15:00-16:45 بعدازظهر',
        '16:45-18:00': '16:45-18:00 عصر',
        '07:30-10:10': '7:30-10:10 صبح',
        '10:15-13:30': '10:15-13:30',
        '13:30-16:00': '13:30-16:00 بعدازظهر',
        '16:00-18:30': '16:00-18:30 عصر',
    }
    
    # Get search query
    search_query = request.GET.get('q', '').strip()
    
    try:
        # Get all active floors (not filtered by faculty - rooms and schedules will be filtered)
        floors = Floor.objects.filter(
            is_active=True
        ).prefetch_related(
            'rooms__schedules__teacher',
            'rooms__schedules__course',
            'rooms__schedules__course__faculty'
        ).order_by('floor_number')
        
        # Prepare floor data with rooms and schedules
        floor_data = []
        for floor in floors:
            # Get all active rooms on this floor (not filtered by faculty)
            rooms = floor.rooms.filter(
                is_active=True
            ).order_by('position', 'room_number')
            
            # Organize rooms by position
            left_rooms = []
            right_rooms = []
            
            for room in rooms:
                # Get schedule for this room at selected day and time
                # Support both new time fields and legacy time_slot
                try:
                    from datetime import time as time_obj
                    
                    schedule = None
                    
                    # Try to parse time as HH:MM format (from new class_affairs page)
                    if ':' in time and len(time.split(':')) == 2:
                        try:
                            start_time = time_obj.fromisoformat(time)
                            
                            # Look for schedule with this start_time
                            schedule = ClassSchedule.objects.select_related(
                                'teacher', 'course', 'course__faculty'
                            ).filter(
                                room=room,
                                day_of_week=day,
                                start_time=start_time,
                                is_active=True,
                                course__faculty=faculty
                            ).first()
                        except ValueError:
                            pass
                    
                    # Try to parse time as HH:MM-HH:MM format for new fields
                    if not schedule and '-' in time and len(time.split('-')) == 2:
                        start_str, end_str = time.split('-')
                        try:
                            start_time = time_obj.fromisoformat(start_str)
                            end_time = time_obj.fromisoformat(end_str)
                            
                            # Look for schedule with new time fields
                            schedule = ClassSchedule.objects.select_related(
                                'teacher', 'course', 'course__faculty'
                            ).filter(
                                room=room,
                                day_of_week=day,
                                start_time=start_time,
                                end_time=end_time,
                                is_active=True,
                                course__faculty=faculty
                            ).first()
                        except ValueError:
                            pass
                    
                    # Fallback to legacy time_slot if not found
                    if not schedule:
                        schedule = ClassSchedule.objects.select_related(
                            'teacher', 'course', 'course__faculty'
                        ).filter(
                            room=room,
                            day_of_week=day,
                            time_slot=time,
                            is_active=True,
                            course__faculty=faculty
                        ).first()
                except ClassSchedule.DoesNotExist:
                    schedule = None
                
                # Apply search filter if query exists
                if search_query and schedule:
                    teacher_match = schedule.teacher and search_query.lower() in schedule.teacher.full_name.lower()
                    course_match = search_query.lower() in schedule.course.course_name.lower()
                    if not (teacher_match or course_match):
                        schedule = None  # Hide this room if it doesn't match search
                
                room_info = {
                    'room': room,
                    'schedule': schedule,
                }
                
                # Categorize by position
                if room.position == 'left':
                    left_rooms.append(room_info)
                elif room.position == 'right':
                    right_rooms.append(room_info)
                elif room.position == 'center':
                    # Distribute center rooms between left and right columns
                    # Alternate between left and right for better visual balance
                    if len(left_rooms) <= len(right_rooms):
                        left_rooms.append(room_info)
                    else:
                        right_rooms.append(room_info)
                else:
                    # Default to left column for unknown positions
                    left_rooms.append(room_info)
            
            # Sort rooms by room number (convert to int for proper sorting)
            def sort_key(room_info):
                try:
                    # Extract number from room number (e.g., "101" from "101" or "Room 101")
                    room_num = room_info['room'].room_number
                    # Extract digits only
                    import re
                    numbers = re.findall(r'\d+', room_num)
                    return int(numbers[0]) if numbers else 0
                except:
                    return 0
            
            left_rooms.sort(key=sort_key)
            right_rooms.sort(key=sort_key)
            
            # Filter out empty rooms when searching
            if search_query:
                # When searching, only show rooms that have matching schedules
                left_rooms = [room for room in left_rooms if room['schedule']]
                right_rooms = [room for room in right_rooms if room['schedule']]
            
            # Only include floor if it has rooms with schedules (when searching) or any rooms (when not searching)
            if not search_query or any(room['schedule'] for room in left_rooms + right_rooms):
                floor_data.append({
                    'floor': floor,
                    'left_rooms': left_rooms,
                    'right_rooms': right_rooms,
                })
        
        # Format time display - handle both new and legacy formats
        if ':' in time and '-' not in time:
            # New format: HH:MM
            try:
                from datetime import time as time_obj
                start_time = time_obj.fromisoformat(time)
                time_display = f"{time} - زمان شروع"
            except ValueError:
                time_display = time
        elif '-' in time:
            # Legacy format: HH:MM-HH:MM
            time_display = time_names.get(time, time)
        else:
            time_display = time
        
        context = {
            'page_title': f'برنامه کلاسی - {day_names[day]} - {time_display}',
            'faculty': faculty,
            'selected_day': day,
            'selected_time': time,
            'day_name': day_names[day],
            'time_name': time_display,
            'floor_data': floor_data,
            'search_query': search_query,
        }
        
        return render(request, 'classes/floor_view.html', context)
        
    except Exception as e:
        # Handle any unexpected errors with detailed logging
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Floor view error for faculty {faculty_id}, day {day}, time {time}: {str(e)}", 
                    exc_info=True)
        
        context = {
            'error': f'خطا در بارگذاری اطلاعات: {str(e)}',
            'faculty_id': faculty_id,
            'day': day,
            'time': time
        }
        return render(request, 'classes/error.html', context, status=500)


def teacher_classes_view(request, day):
    """
    Show all classes for a specific teacher on a specific day.
    
    This view is used for the quick search feature on the home page.
    It displays all time slots where the teacher has classes on the selected day.
    
    Args:
        request: Django HTTP request object with 'q' parameter for teacher name
        day: Selected day of the week
        
    Returns:
        Rendered template with teacher's classes for that day
    """
    
    # Validate day parameter
    valid_days = ['saturday', 'sunday', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday']
    if day not in valid_days:
        context = {
            'error': 'روز انتخاب شده معتبر نیست.'
        }
        return render(request, 'classes/error.html', context, status=400)
    
    # Get search query (teacher name)
    teacher_name = request.GET.get('q', '').strip()
    
    if not teacher_name:
        context = {
            'error': 'لطفاً نام استاد را وارد کنید.'
        }
        return render(request, 'classes/error.html', context, status=400)
    
    # Day names in Persian
    day_names = {
        'saturday': 'شنبه',
        'sunday': 'یکشنبه',
        'monday': 'دوشنبه',
        'tuesday': 'سه‌شنبه',
        'wednesday': 'چهارشنبه',
        'thursday': 'پنجشنبه',
        'friday': 'جمعه',
    }
    
    try:
        # Search for the teacher's classes on this day
        classes = ClassSchedule.objects.filter(
            day_of_week=day,
            is_active=True,
            teacher__full_name__icontains=teacher_name
        ).select_related('teacher', 'course', 'room', 'room__floor').order_by('start_time', 'time_slot', 'room__floor__floor_number')
        
        if not classes.exists():
            # No classes found for this teacher on this day
            context = {
                'page_title': f'نتیجه جستجو - {teacher_name}',
                'teacher_name': teacher_name,
                'day': day,
                'day_name': day_names[day],
                'classes': [],
                'message': f'هیچ کلاسی برای استاد "{teacher_name}" در روز {day_names[day]} یافت نشد.',
            }
            return render(request, 'classes/teacher_classes.html', context)
        
        # Group classes by time display (using new method)
        time_slots = {}
        for class_schedule in classes:
            time_display = class_schedule.get_time_display()
            if time_display not in time_slots:
                time_slots[time_display] = []
            time_slots[time_display].append(class_schedule)
        
        context = {
            'page_title': f'برنامه کلاسی {teacher_name} - {day_names[day]}',
            'teacher_name': teacher_name,
            'day': day,
            'day_name': day_names[day],
            'time_slots': time_slots,
            'classes': classes,
        }
        
        return render(request, 'classes/teacher_classes.html', context)
        
    except Exception as e:
        context = {
            'error': f'خطا در بارگذاری اطلاعات: {str(e)}'
        }
        return render(request, 'classes/error.html', context, status=500)


def error_404(request, exception):
    """Custom 404 error handler"""
    context = {
        'error': 'صفحه مورد نظر یافت نشد.'
    }
    return render(request, 'classes/error.html', context, status=404)


def error_500(request):
    """Custom 500 error handler"""
    context = {
        'error': 'خطای سرور رخ داده است. لطفاً بعداً تلاش کنید.'
    }
    return render(request, 'classes/error.html', context, status=500)


@require_http_methods(["GET"])
def search_api(request):
    """
    API endpoint for Elasticsearch-powered search.
    
    Supports searching for courses and teachers with autocomplete.
    
    Query Parameters:
        q: Search query
        type: 'course' or 'teacher' or 'all' (default: 'all')
        faculty_id: Filter courses by faculty (optional)
        autocomplete: 'true' for autocomplete mode (default: 'false')
        
    Returns:
        JSON response with search results
    """
    query = request.GET.get('q', '').strip()
    search_type = request.GET.get('type', 'all')
    faculty_id = request.GET.get('faculty_id')
    autocomplete = request.GET.get('autocomplete', 'false').lower() == 'true'
    
    if not query:
        return JsonResponse({'results': [], 'error': 'Query parameter is required'}, status=400)
    
    try:
        # Convert faculty_id to int if provided
        if faculty_id:
            try:
                faculty_id = int(faculty_id)
            except ValueError:
                faculty_id = None
        
        # Autocomplete mode
        if autocomplete:
            if search_type == 'course':
                results = autocomplete_courses(query, faculty_id, limit=10)
            elif search_type == 'teacher':
                results = autocomplete_teachers(query, limit=10)
            else:
                # Combined autocomplete
                results = {
                    'courses': autocomplete_courses(query, faculty_id, limit=5),
                    'teachers': autocomplete_teachers(query, limit=5),
                }
            return JsonResponse({'results': results})
        
        # Full search mode
        if search_type == 'course':
            search_results = search_courses(query, faculty_id)[:20]
            results = [
                {
                    'id': hit.id,
                    'course_code': hit.course_code,
                    'course_name': hit.course_name,
                    'credit_hours': hit.credit_hours,
                    'description': hit.description if hasattr(hit, 'description') else None,
                    'faculty': {
                        'id': hit.faculty.id if hasattr(hit, 'faculty') else None,
                        'name': hit.faculty.faculty_name if hasattr(hit, 'faculty') else None,
                    },
                }
                for hit in search_results
            ]
        elif search_type == 'teacher':
            search_results = search_teachers(query)[:20]
            results = [
                {
                    'id': hit.id,
                    'full_name': hit.full_name,
                    'email': hit.email if hasattr(hit, 'email') else None,
                    'phone_number': hit.phone_number if hasattr(hit, 'phone_number') else None,
                    'specialization': hit.specialization if hasattr(hit, 'specialization') else None,
                }
                for hit in search_results
            ]
        else:
            # Search all types
            from .search import search_all
            all_results = search_all(query, faculty_id)
            
            results = {
                'courses': [
                    {
                        'id': hit.id,
                        'course_code': hit.course_code,
                        'course_name': hit.course_name,
                        'credit_hours': hit.credit_hours,
                        'faculty': {
                            'id': hit.faculty.id if hasattr(hit, 'faculty') else None,
                            'name': hit.faculty.faculty_name if hasattr(hit, 'faculty') else None,
                        },
                    }
                    for hit in all_results['courses']
                ],
                'teachers': [
                    {
                        'id': hit.id,
                        'full_name': hit.full_name,
                        'specialization': hit.specialization if hasattr(hit, 'specialization') else None,
                    }
                    for hit in all_results['teachers']
                ],
            }
        
        return JsonResponse({'results': results, 'query': query})
        
    except Exception as e:
        return JsonResponse({'error': str(e), 'results': []}, status=500)


def search_view(request):
    """
    Search page view with Elasticsearch integration.
    
    Displays search form and results for courses and teachers.
    
    Args:
        request: Django HTTP request object
        
    Returns:
        Rendered search.html template with results
    """
    query = request.GET.get('q', '').strip()
    search_type = request.GET.get('type', 'all')
    faculty_id = request.GET.get('faculty_id')
    
    context = {
        'page_title': 'جستجو',
        'query': query,
        'search_type': search_type,
        'faculties': Faculty.objects.filter(is_active=True).order_by('faculty_name'),
    }
    
    if query:
        try:
            # Convert faculty_id to int if provided
            if faculty_id:
                try:
                    faculty_id = int(faculty_id)
                    context['selected_faculty_id'] = faculty_id
                except ValueError:
                    faculty_id = None
            
            # Perform search based on type
            if search_type == 'course':
                search_results = search_courses(query, faculty_id)[:50]
                # Convert to Course objects for template
                course_ids = [hit.id for hit in search_results]
                courses = Course.objects.filter(id__in=course_ids, is_active=True).select_related('faculty')
                context['courses'] = courses
                
            elif search_type == 'teacher':
                search_results = search_teachers(query)[:50]
                # Convert to Teacher objects for template
                teacher_ids = [hit.id for hit in search_results]
                teachers = Teacher.objects.filter(id__in=teacher_ids, is_active=True)
                context['teachers'] = teachers
                
            else:
                # Search all
                from .search import search_all
                all_results = search_all(query, faculty_id)
                
                # Convert to model objects
                course_ids = [hit.id for hit in all_results['courses']]
                teacher_ids = [hit.id for hit in all_results['teachers']]
                
                context['courses'] = Course.objects.filter(id__in=course_ids, is_active=True).select_related('faculty')
                context['teachers'] = Teacher.objects.filter(id__in=teacher_ids, is_active=True)
                
        except Exception as e:
            context['error'] = f'خطا در جستجو: {str(e)}'
    
    return render(request, 'classes/search.html', context)


def elasticsearch_teacher_autocomplete(request):
    """
    Elasticsearch-powered teacher autocomplete API endpoint.
    
    Uses Elasticsearch to provide fast, fuzzy-matching autocomplete
    suggestions for teacher names with faculty information.
    
    Args:
        request: Django HTTP request object with 'q' parameter
        
    Returns:
        JsonResponse with list of matching teachers
        
    Example Response:
        {
            "results": [
                {
                    "id": 1,
                    "full_name": "دکتر احمدی",
                    "faculty_name": "دانشکده هوش مصنوعی",
                    "email": "ahmadi@example.com"
                },
                ...
            ]
        }
    """
    query = request.GET.get('q', '').strip()
    
    # Minimum query length for performance
    if len(query) < 2:
        return JsonResponse({'results': []})
    
    try:
        # Try Elasticsearch first
        from django.conf import settings
        if hasattr(settings, 'ELASTICSEARCH_DSL_AUTOSYNC') and settings.ELASTICSEARCH_DSL_AUTOSYNC:
            # Use Elasticsearch for fuzzy autocomplete
            es_results = autocomplete_teachers(query, limit=10)
            
            # Get teacher IDs from Elasticsearch results
            if es_results:
                teacher_ids = [result['id'] for result in es_results]
                
                # Fetch full teacher objects from database to get related data
                teachers = Teacher.objects.filter(
                    id__in=teacher_ids,
                    is_active=True
                ).select_related('faculty')
                
                # Create a mapping for quick lookup
                teacher_map = {t.id: t for t in teachers}
                
                results = []
                for es_result in es_results:
                    teacher = teacher_map.get(es_result['id'])
                    if teacher:
                        results.append({
                            'id': teacher.id,
                            'full_name': teacher.full_name,
                            'faculty_name': teacher.faculty.faculty_name if teacher.faculty else None,
                            'email': teacher.email if hasattr(teacher, 'email') and teacher.email else None,
                        })
                
                return JsonResponse({'results': results})
        
        # Fallback to database query
        raise Exception("Elasticsearch not available, using database fallback")
        
    except Exception as e:
        # Fallback to database query if Elasticsearch fails
        print(f"Elasticsearch error: {e}. Falling back to database query.")
        
        teachers = Teacher.objects.filter(
            Q(full_name__icontains=query),
            is_active=True
        ).select_related('faculty')[:10]
        
        results = []
        for teacher in teachers:
            results.append({
                'id': teacher.id,
                'full_name': teacher.full_name,
                'faculty_name': teacher.faculty.faculty_name if teacher.faculty else None,
                'email': teacher.email if hasattr(teacher, 'email') and teacher.email else None,
            })
        
        return JsonResponse({'results': results})


@csrf_exempt
@require_http_methods(["POST"])
def vote_class_cancellation(request):
    """
    API endpoint for students to vote that a class won't be held.
    
    Requires 3+ votes to mark class as not holding for 24 hours.
    Uses IP + User Agent hash to prevent duplicate voting.
    Implements balanced voting - removes one opposite vote when voting.
    
    Returns:
        JsonResponse with both vote counts and updated status
    """
    try:
        data = json.loads(request.body)
        schedule_id = data.get('schedule_id')
        
        if not schedule_id:
            return JsonResponse({'success': False, 'error': 'Schedule ID is required'}, status=400)
        
        # Get the schedule
        schedule = get_object_or_404(ClassSchedule, id=schedule_id, is_active=True)
        
        # Create unique identifier for this voter (IP + User Agent)
        ip_address = request.META.get('REMOTE_ADDR', '')
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        voter_identifier = hashlib.sha256(f"{ip_address}{user_agent}cancellation".encode()).hexdigest()
        
        # Check if already voted
        existing_vote = ClassCancellationVote.objects.filter(
            schedule=schedule,
            voter_identifier=voter_identifier,
            voted_at__gte=timezone.now() - timedelta(hours=24)
        ).first()
        
        if existing_vote:
            return JsonResponse({
                'success': False,
                'error': 'شما قبلاً رای داده‌اید',
                'already_voted': True,
                'vote_count': schedule.get_cancellation_vote_count()
            })
        
        # Create new cancellation vote
        ClassCancellationVote.objects.create(
            schedule=schedule,
            voter_identifier=voter_identifier,
            ip_address=ip_address
        )
        
        # IMPORTANT: Remove one confirmation vote if exists (balancing mechanism)
        # This creates a competitive voting system where opposite votes cancel each other
        recent_confirmation_votes = ClassConfirmationVote.objects.filter(
            schedule=schedule,
            voted_at__gte=timezone.now() - timedelta(hours=24)
        ).order_by('voted_at')
        
        if recent_confirmation_votes.exists():
            # Remove the oldest confirmation vote
            oldest_confirmation = recent_confirmation_votes.first()
            oldest_confirmation.delete()
        
        # Update schedule status
        schedule.check_and_update_holding_status()
        
        # Get updated vote counts
        vote_count = schedule.get_cancellation_vote_count()
        confirm_count = schedule.get_confirmation_vote_count()
        
        return JsonResponse({
            'success': True,
            'vote_count': vote_count,
            'confirm_vote_count': confirm_count,  # Send both counts for UI update
            'threshold_reached': vote_count >= 3,
            'student_reported_not_holding': schedule.student_reported_not_holding,
            'message': f'رای شما ثبت شد. رای‌های عدم برگزاری: {vote_count} | رای‌های تأیید: {confirm_count}'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def vote_class_confirmation(request):
    """
    API endpoint for students to vote that a class WILL be held.
    
    Opposite of cancellation vote - confirms class is happening.
    Requires 3+ votes to mark class as confirmed for 24 hours.
    Uses IP + User Agent hash to prevent duplicate voting.
    
    Args:
        request: Django HTTP request with JSON body containing schedule_id
        
    Returns:
        JsonResponse with vote result and current status
        
    Example Response:
        {
            "success": true,
            "vote_count": 5,
            "threshold_reached": true,
            "student_reported_holding": true,
            "message": "رای شما ثبت شد. مجموع رای‌های تأیید برگزاری: 5"
        }
    """
    try:
        data = json.loads(request.body)
        schedule_id = data.get('schedule_id')
        
        if not schedule_id:
            return JsonResponse({'success': False, 'error': 'Schedule ID is required'}, status=400)
        
        # Get the schedule
        schedule = get_object_or_404(ClassSchedule, id=schedule_id, is_active=True)
        
        # Create unique identifier for this voter (IP + User Agent)
        ip_address = request.META.get('REMOTE_ADDR', '')
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        voter_identifier = hashlib.sha256(f"{ip_address}{user_agent}confirmation".encode()).hexdigest()
        
        # Check if already voted for confirmation
        existing_vote = ClassConfirmationVote.objects.filter(
            schedule=schedule,
            voter_identifier=voter_identifier,
            voted_at__gte=timezone.now() - timedelta(hours=24)
        ).first()
        
        if existing_vote:
            return JsonResponse({
                'success': False,
                'error': 'شما قبلاً رای داده‌اید',
                'already_voted': True,
                'vote_count': schedule.get_confirmation_vote_count()
            })
        
        # Create new confirmation vote
        ClassConfirmationVote.objects.create(
            schedule=schedule,
            voter_identifier=voter_identifier,
            ip_address=ip_address
        )
        
        # IMPORTANT: Remove one cancellation vote if exists (balancing mechanism)
        # This creates a competitive voting system where opposite votes cancel each other
        recent_cancellation_votes = ClassCancellationVote.objects.filter(
            schedule=schedule,
            voted_at__gte=timezone.now() - timedelta(hours=24)
        ).order_by('voted_at')
        
        if recent_cancellation_votes.exists():
            # Remove the oldest cancellation vote
            oldest_cancellation = recent_cancellation_votes.first()
            oldest_cancellation.delete()
        
        # Update schedule status
        schedule.check_and_update_holding_status()
        
        # Get updated vote counts
        vote_count = schedule.get_confirmation_vote_count()
        cancel_count = schedule.get_cancellation_vote_count()
        
        return JsonResponse({
            'success': True,
            'vote_count': vote_count,
            'cancel_vote_count': cancel_count,  # Send both counts for UI update
            'threshold_reached': vote_count >= 3,
            'student_reported_holding': schedule.student_reported_holding,
            'message': f'رای شما ثبت شد. رای‌های تأیید: {vote_count} | رای‌های عدم برگزاری: {cancel_count}'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
