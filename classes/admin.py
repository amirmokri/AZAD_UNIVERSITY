"""
Django admin configuration for class scheduling system.

This module customizes the admin panel to provide:
- Enhanced UI/UX for managing schedules
- Filters and search functionality
- Inline editing capabilities
- List displays with relevant information
- Custom actions for bulk operations

All admin classes are optimized for Persian/Farsi language.
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import path, reverse
from django.contrib import messages
from django.http import JsonResponse
from django.template.response import TemplateResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Faculty, Teacher, Course, Floor, Room, ClassSchedule, ClassCancellationVote, ClassConfirmationVote, ImportJob


@admin.register(Faculty)
class FacultyAdmin(admin.ModelAdmin):
    """
    Admin configuration for Faculty model.
    Manages university faculties/departments.
    """
    
    list_display = ['faculty_code', 'faculty_name', 'image_preview', 'course_count', 'is_active_badge', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['faculty_code', 'faculty_name']
    ordering = ['faculty_code']
    list_per_page = 25
    
    fieldsets = (
        ('اطلاعات دانشکده', {
            'fields': ('faculty_code', 'faculty_name')
        }),
        ('تصویر دانشکده', {
            'fields': ('faculty_image',),
            'description': 'نام فایل تصویر را وارد کنید (مثال: AI.jpg یا روانشناسی.webp). فایل باید در پوشه static/images/ قرار گیرد.'
        }),
        ('توضیحات', {
            'fields': ('description',),
            'classes': ('collapse',)
        }),
        ('وضعیت', {
            'fields': ('is_active',)
        }),
    )
    
    def image_preview(self, obj):
        """Display image preview if exists"""
        if obj.faculty_image:
            return format_html(
                '<img src="/static/images/{}" style="width: 50px; height: 50px; object-fit: cover; border-radius: 8px;" />',
                obj.faculty_image
            )
        return format_html('<span style="font-size: 2rem;">🏛️</span>')
    image_preview.short_description = 'تصویر'
    
    def course_count(self, obj):
        """Display number of courses in this faculty"""
        count = obj.courses.count()
        return format_html('<span style="color: blue;">{} درس</span>', count)
    course_count.short_description = 'تعداد دروس'
    
    def is_active_badge(self, obj):
        """Display active status as colored badge"""
        if obj.is_active:
            return format_html('<span style="color: green;">✓ فعال</span>')
        return format_html('<span style="color: red;">✗ غیرفعال</span>')
    is_active_badge.short_description = 'وضعیت'


@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    """
    Admin configuration for Teacher model.
    Provides comprehensive management of teacher records.
    """
    
    list_display = ['full_name', 'faculty_badge', 'email', 'phone_number', 'specialization', 'class_count', 'is_active_badge', 'created_at']
    list_filter = ['faculty', 'is_active', 'created_at', 'specialization']
    search_fields = ['full_name', 'email', 'phone_number', 'specialization', 'faculty__faculty_name']
    ordering = ['faculty', 'full_name']
    list_per_page = 30
    
    def faculty_badge(self, obj):
        """Display faculty as badge"""
        if obj.faculty:
            return format_html(
                '<span style="background: #17a2b8; color: white; padding: 5px 10px; border-radius: 12px; font-size: 0.85rem;">{}</span>',
                obj.faculty.faculty_name
            )
        return format_html('<span style="background: #dc3545; color: white; padding: 5px 10px; border-radius: 12px; font-size: 0.85rem;">بدون دانشکده</span>')
    faculty_badge.short_description = 'دانشکده'
    faculty_badge.admin_order_field = 'faculty'
    
    def class_count(self, obj):
        """Display number of classes taught by this teacher"""
        count = obj.schedules.filter(is_active=True).count()
        if count > 0:
            return format_html('<span style="color: blue; font-weight: bold;">{} کلاس</span>', count)
        return format_html('<span style="color: #999;">-</span>')
    class_count.short_description = 'تعداد کلاس‌ها'
    
    fieldsets = (
        ('دانشکده', {
            'fields': ('faculty',),
            'description': 'دانشکده‌ای که این استاد در آن تدریس می‌کند'
        }),
        ('اطلاعات اصلی', {
            'fields': ('full_name', 'email', 'phone_number', 'specialization')
        }),
        ('وضعیت', {
            'fields': ('is_active',)
        }),
    )
    
    def is_active_badge(self, obj):
        """Display active status as colored badge"""
        if obj.is_active:
            return format_html('<span style="color: green;">✓ فعال</span>')
        return format_html('<span style="color: red;">✗ غیرفعال</span>')
    is_active_badge.short_description = 'وضعیت'
    
    actions = ['activate_teachers', 'deactivate_teachers']
    
    def activate_teachers(self, request, queryset):
        """Bulk action to activate selected teachers"""
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} استاد فعال شد.')
    activate_teachers.short_description = 'فعال کردن اساتید انتخاب شده'
    
    def deactivate_teachers(self, request, queryset):
        """Bulk action to deactivate selected teachers"""
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} استاد غیرفعال شد.')
    deactivate_teachers.short_description = 'غیرفعال کردن اساتید انتخاب شده'


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    """
    Admin configuration for Course model.
    Manages course information with search and filtering.
    """
    
    list_display = ['course_code', 'course_name', 'faculty_badge', 'credit_hours', 'schedule_count', 'is_active_badge', 'created_at']
    list_filter = ['is_active', 'faculty', 'credit_hours', 'created_at']
    search_fields = ['course_code', 'course_name', 'faculty__faculty_name']
    ordering = ['faculty', 'course_code']
    list_per_page = 30
    
    fieldsets = (
        ('دانشکده', {
            'fields': ('faculty',),
            'description': 'دانشکده مربوط به این درس را انتخاب کنید'
        }),
        ('اطلاعات درس', {
            'fields': ('course_code', 'course_name', 'credit_hours'),
            'description': 'کد درس باید یکتا باشد'
        }),
        ('جزئیات', {
            'fields': ('description',),
            'classes': ('collapse',)
        }),
        ('وضعیت', {
            'fields': ('is_active',)
        }),
    )
    
    def faculty_badge(self, obj):
        """Display faculty as badge"""
        if obj.faculty:
            return format_html(
                '<span style="background: #28a745; color: white; padding: 5px 10px; border-radius: 12px; font-size: 0.85rem;">{}</span>',
                obj.faculty.faculty_name
            )
        return format_html('<span style="background: #dc3545; color: white; padding: 5px 10px; border-radius: 12px; font-size: 0.85rem;">بدون دانشکده</span>')
    faculty_badge.short_description = 'دانشکده'
    faculty_badge.admin_order_field = 'faculty'
    
    def schedule_count(self, obj):
        """Display number of schedules for this course"""
        count = obj.schedules.filter(is_active=True).count()
        if count > 0:
            return format_html('<span style="color: blue; font-weight: bold;">{} کلاس</span>', count)
        return format_html('<span style="color: #999;">-</span>')
    schedule_count.short_description = 'تعداد کلاس‌ها'
    
    def is_active_badge(self, obj):
        """Display active status as colored badge"""
        if obj.is_active:
            return format_html('<span style="color: green;">✓ فعال</span>')
        return format_html('<span style="color: red;">✗ غیرفعال</span>')
    is_active_badge.short_description = 'وضعیت'


@admin.register(Floor)
class FloorAdmin(admin.ModelAdmin):
    """
    Admin configuration for Floor model.
    Displays floors with room count.
    """
    
    list_display = ['floor_number', 'floor_name', 'faculty_badge', 'room_count', 'is_active_badge']
    list_filter = ['faculty', 'is_active']
    search_fields = ['floor_name', 'faculty__faculty_name']
    ordering = ['faculty', 'floor_number']
    
    fieldsets = (
        ('دانشکده', {
            'fields': ('faculty',),
            'description': 'دانشکده‌ای که این طبقه به آن تعلق دارد'
        }),
        ('اطلاعات طبقه', {
            'fields': ('floor_number', 'floor_name')
        }),
        ('توضیحات', {
            'fields': ('description',),
            'classes': ('collapse',)
        }),
        ('وضعیت', {
            'fields': ('is_active',)
        }),
    )
    
    def faculty_badge(self, obj):
        """Display faculty as badge"""
        if obj.faculty:
            return format_html(
                '<span style="background: #6f42c1; color: white; padding: 5px 10px; border-radius: 12px; font-size: 0.85rem;">{}</span>',
                obj.faculty.faculty_name
            )
        return format_html('<span style="background: #dc3545; color: white; padding: 5px 10px; border-radius: 12px; font-size: 0.85rem;">بدون دانشکده</span>')
    faculty_badge.short_description = 'دانشکده'
    faculty_badge.admin_order_field = 'faculty'
    
    def room_count(self, obj):
        """Display number of rooms on this floor"""
        count = obj.rooms.count()
        return format_html('<span style="color: blue;">{} اتاق</span>', count)
    room_count.short_description = 'تعداد اتاق‌ها'
    
    def is_active_badge(self, obj):
        """Display active status as colored badge"""
        if obj.is_active:
            return format_html('<span style="color: green;">✓ فعال</span>')
        return format_html('<span style="color: red;">✗ غیرفعال</span>')
    is_active_badge.short_description = 'وضعیت'


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    """
    Admin configuration for Room model.
    Comprehensive room management with floor filtering.
    """
    
    list_display = ['room_number', 'floor', 'faculty_badge', 'room_type_display', 'capacity', 'position_display', 'schedule_count', 'is_active_badge']
    list_filter = ['faculty', 'floor', 'room_type', 'position', 'is_active']
    search_fields = ['room_number', 'faculty__faculty_name', 'floor__floor_name']
    ordering = ['faculty', 'floor__floor_number', 'room_number']
    list_per_page = 30
    
    fieldsets = (
        ('دانشکده', {
            'fields': ('faculty',),
            'description': 'دانشکده (اگر خالی باشد، به صورت خودکار از طبقه تعیین می‌شود)'
        }),
        ('اطلاعات اصلی', {
            'fields': ('floor', 'room_number', 'room_type')
        }),
        ('ویژگی‌ها', {
            'fields': ('capacity', 'position')
        }),
        ('وضعیت', {
            'fields': ('is_active',)
        }),
    )
    
    def faculty_badge(self, obj):
        """Display faculty as badge"""
        if obj.faculty:
            return format_html(
                '<span style="background: #fd7e14; color: white; padding: 5px 10px; border-radius: 12px; font-size: 0.85rem;">{}</span>',
                obj.faculty.faculty_name
            )
        return format_html('<span style="background: #dc3545; color: white; padding: 5px 10px; border-radius: 12px; font-size: 0.85rem;">بدون دانشکده</span>')
    faculty_badge.short_description = 'دانشکده'
    faculty_badge.admin_order_field = 'faculty'
    
    def room_type_display(self, obj):
        """Display room type in Persian"""
        return obj.get_room_type_display()
    room_type_display.short_description = 'نوع اتاق'
    
    def position_display(self, obj):
        """Display position in Persian"""
        return obj.get_position_display()
    position_display.short_description = 'موقعیت'
    
    def schedule_count(self, obj):
        """Display number of schedules for this room"""
        count = obj.schedules.filter(is_active=True).count()
        return format_html('<span style="color: blue;">{} برنامه</span>', count)
    schedule_count.short_description = 'تعداد برنامه‌ها'
    
    def is_active_badge(self, obj):
        """Display active status as colored badge"""
        if obj.is_active:
            return format_html('<span style="color: green;">✓ فعال</span>')
        return format_html('<span style="color: red;">✗ غیرفعال</span>')
    is_active_badge.short_description = 'وضعیت'


@admin.register(ClassSchedule)
class ClassScheduleAdmin(admin.ModelAdmin):
    change_list_template = 'admin/schedules/classschedule_changelist.html'
    """
    Admin configuration for ClassSchedule model.
    Main admin interface for managing class schedules.
    Includes comprehensive filtering and search capabilities.
    """
    
    list_display = [
        'schedule_summary',
        'faculty_display',
        'teacher',
        'room_info',
        'day_display',
        'time_display_new',
        'is_holding_badge',
        'student_votes_display',
        'semester',
        'is_active_badge'
    ]
    
    def get_urls(self):
        """Add custom chart view URLs."""
        urls = super().get_urls()
        custom_urls = [
            # Chart flow: day selection -> floor selection -> chart display
            path('chart/', self.admin_site.admin_view(self.day_selection_view), name='classes_classschedule_chart'),
            path('chart/day/', self.admin_site.admin_view(self.day_selection_view), name='classes_classschedule_day_selection'),
            path('chart/day/<str:day>/', self.admin_site.admin_view(self.floor_selection_view), name='classes_classschedule_floor_selection'),
            path('chart/day/<str:day>/floor/<int:floor>/', self.admin_site.admin_view(self.chart_view), name='classes_classschedule_chart_floor'),
            # CSV export URLs
            path('chart/export-csv/day/<str:day>/floor/<int:floor>/', self.admin_site.admin_view(self.chart_export_csv), name='classes_classschedule_chart_export_csv_floor'),
            path('chart/export-csv/day/<str:day>/', self.admin_site.admin_view(self.chart_export_csv), name='classes_classschedule_chart_export_csv_day'),
            path('chart/export-csv/', self.admin_site.admin_view(self.chart_export_csv), name='classes_classschedule_chart_export_csv'),
            # Other chart actions
            path('chart/save/', self.admin_site.admin_view(self.save_schedule_view), name='classes_classschedule_save'),
            path('chart/delete/', self.admin_site.admin_view(self.delete_schedule_view), name='classes_classschedule_delete'),
            path('import-excel/', self.admin_site.admin_view(self.import_excel_view), name='classes_classschedule_import_excel'),
        ]
        return custom_urls + urls
    
    def changelist_view(self, request, extra_context=None):
        """Add chart link to changelist view."""
        extra_context = extra_context or {}
        extra_context['chart_url'] = reverse('admin:classes_classschedule_chart')
        return super().changelist_view(request, extra_context)

    def import_excel_view(self, request):
        """Upload form and execution for Excel import."""
        from django import forms
        from django.core.files.storage import default_storage
        from django.core.files.base import ContentFile
        from schedules.importers.ai_excel_importer import import_ai_excel

        class ImportForm(forms.Form):
            faculty = forms.ModelChoiceField(queryset=Faculty.objects.filter(is_active=True), label='دانشکده', required=True)
            semester = forms.CharField(label='نیمسال', required=True)
            academic_year = forms.CharField(label='سال تحصیلی', required=True)
            excel = forms.FileField(label='فایل اکسل', required=True)
            dry_run = forms.BooleanField(label='اجرای آزمایشی', required=False, initial=True)

        context = {
            **self.admin_site.each_context(request),
            'title': 'درون‌ریزی از اکسل',
            'opts': self.model._meta,
        }

        if request.method == 'POST':
            form = ImportForm(request.POST, request.FILES)
            if form.is_valid():
                faculty = form.cleaned_data['faculty']
                semester = form.cleaned_data['semester']
                academic_year = form.cleaned_data['academic_year']
                dry_run = form.cleaned_data.get('dry_run', True)
                f = form.cleaned_data['excel']

                # Save to media/imports/
                save_path = default_storage.save(f"imports/{f.name}", ContentFile(f.read()))
                # Execute importer synchronously
                result = import_ai_excel(default_storage.path(save_path), faculty, semester, academic_year, dry_run)

                prefix = '[Dry Run] ' if dry_run else ''
                self.message_user(
                    request,
                    f"{prefix}درون‌ریزی انجام شد: جدید {result['inserted']}, بروزرسانی {result['updated']}, کل {result['total']}. خطاها: {len(result['errors'])}",
                    level=messages.SUCCESS,
                )
                return JsonResponse({'success': True})
        else:
            form = ImportForm()

        context['form'] = form
        return TemplateResponse(request, 'admin/schedules/import_excel.html', context)
    
    list_filter = [
        'course__faculty',
        'day_of_week',
        'start_time',
        'end_time',
        'is_holding',
        'is_active',
        'semester',
        'academic_year',
        'room__floor',
        'teacher',
    ]
    
    search_fields = [
        'course__course_name',
        'course__course_code',
        'course__faculty__faculty_name',
        'teacher__full_name',
        'room__room_number',
    ]
    
    ordering = ['course__faculty', 'day_of_week', 'start_time']
    list_per_page = 50
    
    fieldsets = (
        ('اطلاعات درس', {
            'fields': ('course',),
            'description': 'درس را انتخاب کنید (دانشکده به صورت خودکار از درس تعیین می‌شود)'
        }),
        ('استاد و اتاق', {
            'fields': ('teacher', 'room')
        }),
        ('زمان‌بندی', {
            'fields': ('day_of_week', 'start_time', 'end_time', 'time_slot'),
            'description': 'روز و زمان برگزاری کلاس (از ساعت شروع و پایان استفاده کنید)'
        }),
        ('دوره تحصیلی', {
            'fields': ('semester', 'academic_year'),
            'classes': ('collapse',),
            'description': 'اطلاعات ترم و سال تحصیلی'
        }),
        ('یادداشت‌ها', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
        ('وضعیت', {
            'fields': ('is_holding', 'is_active'),
            'description': 'وضعیت برگزاری و فعال بودن کلاس'
        }),
    )
    
    autocomplete_fields = ['teacher', 'course', 'room']
    
    def schedule_summary(self, obj):
        """Display schedule summary"""
        return format_html(
            '<strong>{}</strong><br/><small>کد: {}</small><br/>{}',
            obj.course.course_name,
            obj.course.course_code,
            obj.teacher.full_name if obj.teacher else 'بدون استاد'
        )
    schedule_summary.short_description = 'خلاصه برنامه'
    
    def faculty_display(self, obj):
        """Display faculty name"""
        if obj.course and obj.course.faculty:
            return format_html(
                '<span style="background: #1e3c72; color: white; padding: 5px 10px; border-radius: 12px; font-size: 0.85rem;">{}</span>',
                obj.course.faculty.faculty_name
            )
        return format_html('<span style="color: red;">بدون دانشکده</span>')
    faculty_display.short_description = 'دانشکده'
    faculty_display.admin_order_field = 'course__faculty'
    
    def room_info(self, obj):
        """Display room information"""
        return format_html(
            '{}<br/><small>ظرفیت: {}</small>',
            obj.room,
            obj.room.capacity
        )
    room_info.short_description = 'اتاق'
    
    def day_display(self, obj):
        """Display day in Persian"""
        return obj.get_day_of_week_display()
    day_display.short_description = 'روز'
    
    def time_display(self, obj):
        """Display time slot in Persian (legacy)"""
        return obj.get_time_slot_display()
    time_display.short_description = 'زمان (قدیمی)'
    
    def time_display_new(self, obj):
        """Display start and end time in HH:MM format"""
        if obj.start_time and obj.end_time:
            duration = obj.get_duration_hours() or 0
            # Avoid {:.1f} in format_html (SafeString), format first then pass
            duration_text = f"{duration:.1f}"
            return format_html(
                '<strong>{} - {}</strong><br/><small>مدت: {} ساعت</small>',
                obj.start_time.strftime('%H:%M'),
                obj.end_time.strftime('%H:%M'),
                duration_text
            )
        elif obj.time_slot:
            return format_html(
                '<span style="color: #666;">{}</span><br/><small>قدیمی</small>',
                obj.time_slot
            )
        else:
            return format_html('<span style="color: red;">زمان نامشخص</span>')
    time_display_new.short_description = 'زمان'
    time_display_new.admin_order_field = 'start_time'
    
    def is_holding_badge(self, obj):
        """Display holding status considering both admin setting and student votes"""
        if obj.student_reported_not_holding:
            return format_html('<span style="color: red; font-weight: bold;">⚠️ دانشجویان: عدم برگزاری</span>')
        elif obj.student_reported_holding:
            return format_html('<span style="color: green; font-weight: bold;">✅ دانشجویان: تأیید برگزاری</span>')
        elif obj.is_holding:
            return format_html('<span style="color: green;">✅ برگزار می‌شود</span>')
        return format_html('<span style="color: orange;">⏸️ برگزار نمی‌شود</span>')
    is_holding_badge.short_description = 'وضعیت برگزاری'
    
    def student_votes_display(self, obj):
        """Display student vote counts (both cancellation and confirmation)"""
        cancel_count = obj.get_cancellation_vote_count()
        confirm_count = obj.get_confirmation_vote_count()
        
        html_parts = []
        
        # Cancellation votes
        if cancel_count >= 3:
            html_parts.append(f'<span style="color: red; font-weight: bold;">{cancel_count} لغو ❌</span>')
        elif cancel_count > 0:
            html_parts.append(f'<span style="color: orange;">{cancel_count} لغو ⚠️</span>')
        
        # Confirmation votes
        if confirm_count >= 3:
            html_parts.append(f'<span style="color: green; font-weight: bold;">{confirm_count} تأیید ✅</span>')
        elif confirm_count > 0:
            html_parts.append(f'<span style="color: blue;">{confirm_count} تأیید ℹ️</span>')
        
        if not html_parts:
            return format_html('<span style="color: #999;">-</span>')
        
        return format_html(' | '.join(html_parts))
    student_votes_display.short_description = 'رای دانشجویان'
    
    def is_active_badge(self, obj):
        """Display active status as colored badge"""
        if obj.is_active:
            return format_html('<span style="color: green;">✓ فعال</span>')
        return format_html('<span style="color: red;">✗ غیرفعال</span>')
    is_active_badge.short_description = 'وضعیت'
    
    def chart_view(self, request, day=None, floor=None):
        """
        Display schedule as an Excel-like chart.
        
        Args:
            request: HTTP request
            day: Day of week filter (required)
            floor: Floor number filter (required)
        """
        # Both day and floor are required for chart display
        if not day or not floor:
            from django.contrib import messages
            messages.error(request, 'روز و طبقه باید انتخاب شوند.')
            from django.shortcuts import redirect
            return redirect('admin:classes_classschedule_chart')
        
        try:
            # Get all days and floors for navigation
            days = ClassSchedule.DAY_CHOICES
            floors = Floor.objects.filter(is_active=True).order_by('floor_number')
            
            # Get all rooms for the selected floor or all floors
            if floor:
                rooms = Room.objects.filter(floor__floor_number=floor, is_active=True).order_by('room_number')
            else:
                rooms = Room.objects.filter(is_active=True).order_by('floor__floor_number', 'room_number')
            
            # Get schedules for the selected day or all days
            schedules_query = ClassSchedule.objects.filter(is_active=True)
            if day:
                schedules_query = schedules_query.filter(day_of_week=day)
            if floor:
                schedules_query = schedules_query.filter(room__floor__floor_number=floor)
            
            schedules = schedules_query.select_related('teacher', 'course', 'room', 'room__floor', 'course__faculty')
            
            # Get all unique time slots from actual schedules
            all_time_slots = set()
            for schedule in schedules:
                if schedule.start_time and schedule.end_time:
                    time_slot = f"{schedule.start_time.strftime('%H:%M')}-{schedule.end_time.strftime('%H:%M')}"
                    all_time_slots.add(time_slot)
                elif schedule.time_slot:
                    all_time_slots.add(schedule.time_slot)
            
            # Sort time slots chronologically
            sorted_time_slots = sorted(all_time_slots)
            
            # Create time slot tuples for template
            time_slots = [(slot, slot) for slot in sorted_time_slots]
            
            # Create a comprehensive mapping of schedules by room and time
            schedule_map = {}
            
            for schedule in schedules:
                room_id = schedule.room.id
                if room_id not in schedule_map:
                    schedule_map[room_id] = {}
                
                # Determine time key - prioritize start_time/end_time over time_slot
                time_key = None
                if schedule.start_time and schedule.end_time:
                    time_key = f"{schedule.start_time.strftime('%H:%M')}-{schedule.end_time.strftime('%H:%M')}"
                elif schedule.time_slot:
                    time_key = schedule.time_slot
                
                if time_key:
                    schedule_map[room_id][time_key] = schedule
            
            # Get courses and teachers for the popup form
            courses = Course.objects.filter(is_active=True).order_by('course_code')
            teachers = Teacher.objects.filter(is_active=True).order_by('full_name')
            
            # Calculate statistics for display
            total_schedules = schedules.count()
            total_rooms = rooms.count()
            active_schedules = schedules.filter(is_holding=True).count()
            
            context = {
                'title': 'نمودار برنامه کلاسی',
                'days': days,
                'floors': floors,
                'rooms': rooms,
                'schedules': schedules,
                'schedule_map': schedule_map,
                'time_slots': time_slots,
                'selected_day': day,
                'selected_floor': floor,
                'courses': courses,
                'teachers': teachers,
                'total_schedules': total_schedules,
                'total_rooms': total_rooms,
                'active_schedules': active_schedules,
                'opts': self.model._meta,
            }
            
            return TemplateResponse(request, 'admin/classes/classschedule/chart.html', context)
            
        except Exception as e:
            # Log error and return error page
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Chart view error: {str(e)}", exc_info=True)
            
            from django.contrib import messages
            messages.error(request, f'خطا در نمایش نمودار: {str(e)}')
            
            # Return to changelist with error
            from django.shortcuts import redirect
            return redirect('admin:classes_classschedule_changelist')
    
    def chart_export_csv(self, request, day=None, floor=None):
        """
        Export schedule chart data to CSV format.
        
        Args:
            request: HTTP request
            day: Day of week filter (optional)
            floor: Floor number filter (optional)
        """
        try:
            import csv
            from django.http import HttpResponse
            from django.utils import timezone
            from django.utils.encoding import force_str
            import io
            
            # Get the same data as chart view
            rooms_query = Room.objects.filter(is_active=True)
            if floor:
                rooms_query = rooms_query.filter(floor__floor_number=floor)
            rooms = rooms_query.order_by('floor__floor_number', 'room_number')
            
            schedules_query = ClassSchedule.objects.filter(is_active=True)
            if day:
                schedules_query = schedules_query.filter(day_of_week=day)
            if floor:
                schedules_query = schedules_query.filter(room__floor__floor_number=floor)
            
            schedules = schedules_query.select_related(
                'teacher', 'course', 'room', 'room__floor', 'course__faculty'
            )
            
            # Create CSV response
            response = HttpResponse(content_type='text/csv; charset=utf-8')
            
            # Generate filename with timestamp and filters
            timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
            filename_parts = ['schedule_chart', timestamp]
            if day:
                day_name = dict(ClassSchedule.DAY_CHOICES).get(day, day)
                filename_parts.append(day_name)
            if floor:
                filename_parts.append(f'floor_{floor}')
            
            filename = '_'.join(filename_parts) + '.csv'
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            
            # Create CSV writer with UTF-8 BOM for Excel compatibility
            response.write('\ufeff')  # UTF-8 BOM
            writer = csv.writer(response)
            
            # Write headers
            headers = [
                'شماره اتاق',
                'طبقه',
                'نوع اتاق',
                'ظرفیت',
                'موقعیت',
                'دانشکده',
                'روز هفته',
                'ساعت شروع',
                'ساعت پایان',
                'بازه زمانی',
                'کد درس',
                'نام درس',
                'واحد درسی',
                'نام استاد',
                'نیمسال',
                'سال تحصیلی',
                'وضعیت برگزاری',
                'یادداشت‌ها',
                'تاریخ ایجاد',
                'تاریخ بروزرسانی'
            ]
            writer.writerow(headers)
            
            # Create a dictionary to map schedules to rooms and time slots
            schedule_map = {}
            for schedule in schedules:
                room_key = schedule.room.id
                time_key = None
                
                # Determine time key based on available time data
                if schedule.start_time and schedule.end_time:
                    time_key = f"{schedule.start_time.strftime('%H:%M')}-{schedule.end_time.strftime('%H:%M')}"
                elif schedule.time_slot:
                    time_key = schedule.time_slot
                
                if time_key:
                    if room_key not in schedule_map:
                        schedule_map[room_key] = {}
                    schedule_map[room_key][time_key] = schedule
            
            # Get all unique time slots from all schedules for comprehensive coverage
            all_time_slots_global = set()
            for schedule in schedules:
                if schedule.start_time and schedule.end_time:
                    time_slot = f"{schedule.start_time.strftime('%H:%M')}-{schedule.end_time.strftime('%H:%M')}"
                    all_time_slots_global.add(time_slot)
                elif schedule.time_slot:
                    all_time_slots_global.add(schedule.time_slot)
            
            # Add standard time slots if none exist
            if not all_time_slots_global:
                all_time_slots_global = {
                    '07:30-09:15', '09:15-11:00', '11:00-13:15', 
                    '13:15-15:00', '15:00-16:45', '16:45-18:00',
                    '07:30-10:10', '10:15-13:30', '13:30-16:00', '16:00-18:30'
                }
            
            # Write data rows
            for room in rooms:
                room_schedules = schedule_map.get(room.id, {})
                
                # Use global time slots for consistent coverage
                sorted_time_slots = sorted(all_time_slots_global)
                
                for time_slot in sorted_time_slots:
                    schedule = room_schedules.get(time_slot)
                    
                    if schedule:
                        # Schedule exists - write full data
                        row = [
                            force_str(room.room_number),
                            force_str(room.floor.floor_number),
                            force_str(room.get_room_type_display()),
                            force_str(room.capacity),
                            force_str(room.get_position_display()),
                            force_str(room.faculty.faculty_name if room.faculty else 'نامشخص'),
                            force_str(schedule.get_day_of_week_display()),
                            force_str(schedule.start_time.strftime('%H:%M') if schedule.start_time else ''),
                            force_str(schedule.end_time.strftime('%H:%M') if schedule.end_time else ''),
                            force_str(time_slot),
                            force_str(schedule.course.course_code),
                            force_str(schedule.course.course_name),
                            force_str(schedule.course.credit_hours),
                            force_str(schedule.teacher.full_name),
                            force_str(schedule.semester or ''),
                            force_str(schedule.academic_year or ''),
                            force_str('برگزار می‌شود' if schedule.is_holding else 'برگزار نمی‌شود'),
                            force_str(schedule.notes or ''),
                            force_str(schedule.created_at.strftime('%Y-%m-%d %H:%M:%S') if schedule.created_at else ''),
                            force_str(schedule.updated_at.strftime('%Y-%m-%d %H:%M:%S') if schedule.updated_at else '')
                        ]
                    else:
                        # No schedule - write room info with empty schedule data
                        row = [
                            force_str(room.room_number),
                            force_str(room.floor.floor_number),
                            force_str(room.get_room_type_display()),
                            force_str(room.capacity),
                            force_str(room.get_position_display()),
                            force_str(room.faculty.faculty_name if room.faculty else 'نامشخص'),
                            force_str(dict(ClassSchedule.DAY_CHOICES).get(day, '') if day else ''),
                            '',  # start_time
                            '',  # end_time
                            force_str(time_slot),
                            '',  # course_code
                            '',  # course_name
                            '',  # credit_hours
                            '',  # teacher_name
                            '',  # semester
                            '',  # academic_year
                            '',  # is_holding
                            '',  # notes
                            '',  # created_at
                            ''   # updated_at
                        ]
                    
                    writer.writerow(row)
            
            return response
            
        except Exception as e:
            # Log the error for debugging
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"CSV export error: {str(e)}", exc_info=True)
            
            # Return user-friendly error response
            from django.http import JsonResponse
            from django.contrib import messages
            
            # Add error message for admin interface
            if hasattr(request, '_messages'):
                messages.error(request, f'خطا در صادرات فایل CSV: {str(e)}')
            
            return JsonResponse({
                'error': 'خطا در تولید فایل CSV',
                'details': 'لطفاً با مدیر سیستم تماس بگیرید یا دوباره تلاش کنید.',
                'technical_details': str(e) if request.user.is_superuser else None
            }, status=500)
    
    def day_selection_view(self, request):
        """
        Day selection view for chart with class statistics.
        """
        days = ClassSchedule.DAY_CHOICES
        day_stats = []
        
        # Get statistics for each day
        for day_value, day_name in days:
            schedules_count = ClassSchedule.objects.filter(
                day_of_week=day_value, 
                is_active=True
            ).count()
            
            active_schedules_count = ClassSchedule.objects.filter(
                day_of_week=day_value, 
                is_active=True,
                is_holding=True
            ).count()
            
            rooms_count = Room.objects.filter(
                schedules__day_of_week=day_value,
                schedules__is_active=True,
                is_active=True
            ).distinct().count()
            
            day_stats.append({
                'value': day_value,
                'name': day_name,
                'schedules_count': schedules_count,
                'active_schedules_count': active_schedules_count,
                'rooms_count': rooms_count
            })
        
        context = {
            'title': 'انتخاب روز هفته',
            'days': days,
            'day_stats': day_stats,
            'opts': self.model._meta,
        }
        return TemplateResponse(request, 'admin/classes/classschedule/day_selection.html', context)
    
    def floor_selection_view(self, request, day):
        """
        Floor selection view for chart after day selection with statistics.
        """
        try:
            # Get day name
            day_choices = dict(ClassSchedule.DAY_CHOICES)
            day_name = day_choices.get(day, day)
            
            # Get floors that have schedules for this day
            floors = Floor.objects.filter(
                rooms__schedules__day_of_week=day,
                rooms__schedules__is_active=True,
                is_active=True
            ).distinct().order_by('floor_number')
            
            floor_stats = []
            for floor in floors:
                schedules_count = ClassSchedule.objects.filter(
                    room__floor=floor,
                    day_of_week=day,
                    is_active=True
                ).count()
                
                active_schedules_count = ClassSchedule.objects.filter(
                    room__floor=floor,
                    day_of_week=day,
                    is_active=True,
                    is_holding=True
                ).count()
                
                rooms_count = Room.objects.filter(
                    floor=floor,
                    schedules__day_of_week=day,
                    schedules__is_active=True,
                    is_active=True
                ).distinct().count()
                
                floor_stats.append({
                    'floor': floor,
                    'schedules_count': schedules_count,
                    'active_schedules_count': active_schedules_count,
                    'rooms_count': rooms_count
                })
            
            context = {
                'title': f'انتخاب طبقه - {day_name}',
                'day': day,
                'day_name': day_name,
                'floors': floors,
                'floor_stats': floor_stats,
                'opts': self.model._meta,
            }
            return TemplateResponse(request, 'admin/classes/classschedule/floor_selection.html', context)
            
        except Exception as e:
            logger.error(f"Floor selection view error: {str(e)}", exc_info=True)
            messages.error(request, f'خطا در نمایش طبقات: {str(e)}')
            return redirect('admin:classes_classschedule_changelist')
    
    actions = ['activate_schedules', 'deactivate_schedules', 'hold_schedules', 'unhold_schedules', 'duplicate_schedule']
    
    def activate_schedules(self, request, queryset):
        """Bulk action to activate selected schedules"""
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} برنامه فعال شد.')
    activate_schedules.short_description = 'فعال کردن برنامه‌های انتخاب شده'
    
    def deactivate_schedules(self, request, queryset):
        """Bulk action to deactivate selected schedules"""
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} برنامه غیرفعال شد.')
    deactivate_schedules.short_description = 'غیرفعال کردن برنامه‌های انتخاب شده'
    
    def hold_schedules(self, request, queryset):
        """Bulk action to mark schedules as holding"""
        updated = queryset.update(is_holding=True)
        self.message_user(request, f'{updated} برنامه به عنوان برگزار شونده علامت‌گذاری شد.')
    hold_schedules.short_description = 'علامت‌گذاری به عنوان برگزار شونده'
    
    def unhold_schedules(self, request, queryset):
        """Bulk action to mark schedules as not holding"""
        updated = queryset.update(is_holding=False)
        self.message_user(request, f'{updated} برنامه به عنوان برگزار نشونده علامت‌گذاری شد.')
    unhold_schedules.short_description = 'علامت‌گذاری به عنوان برگزار نشونده'
    
    def duplicate_schedule(self, request, queryset):
        """Bulk action to duplicate selected schedules (for next semester)"""
        count = 0
        for schedule in queryset:
            schedule.pk = None
            schedule.is_active = False
            try:
                schedule.save()
                count += 1
            except:
                pass
        self.message_user(request, f'{count} برنامه کپی شد (غیرفعال).')
    duplicate_schedule.short_description = 'کپی برداری از برنامه‌های انتخاب شده'
    
    @csrf_exempt
    def save_schedule_view(self, request):
        """AJAX view to save schedule from chart popup."""
        if request.method == 'POST':
            try:
                schedule_id = request.POST.get('schedule_id')
                room_id = request.POST.get('room_id')
                day_of_week = request.POST.get('day_of_week')
                time_slot = request.POST.get('time_slot')
                start_time = request.POST.get('start_time')
                end_time = request.POST.get('end_time')
                course_id = request.POST.get('course')
                teacher_id = request.POST.get('teacher')
                semester = request.POST.get('semester', '')
                academic_year = request.POST.get('academic_year', '')
                is_holding = request.POST.get('is_holding') == 'true'
                notes = request.POST.get('notes', '')
                
                if schedule_id:
                    # Update existing schedule with conflict check
                    schedule = ClassSchedule.objects.get(id=schedule_id)
                    # Prevent moving it into a full line by credit bucket if time/room/day changes
                    intended_room_id = room_id or schedule.room_id
                    intended_day = day_of_week or schedule.day_of_week
                    intended_course_id = course_id or schedule.course_id
                    intended_course = Course.objects.get(id=intended_course_id)
                    intended_credit = intended_course.credit_hours

                    # Use new time fields for conflict checking
                    if start_time and end_time:
                        from datetime import time
                        intended_start = time.fromisoformat(start_time)
                        intended_end = time.fromisoformat(end_time)
                        
                        # Check for time conflicts using new fields
                        existing_schedules = ClassSchedule.objects.filter(
                            room_id=intended_room_id,
                            day_of_week=intended_day,
                            is_active=True
                        ).exclude(pk=schedule.id).select_related('course', 'teacher', 'room', 'room__floor')
                        
                        conflict = None
                        for es in existing_schedules:
                            if es.start_time and es.end_time:
                                # Check for time overlap
                                if not (intended_end <= es.start_time or es.end_time <= intended_start):
                                    conflict = es
                                    break
                    else:
                        # Fallback to old time_slot logic
                        intended_time_slot = time_slot or schedule.time_slot
                        existing_schedules = ClassSchedule.objects.filter(
                            room_id=intended_room_id,
                            day_of_week=intended_day,
                            time_slot=intended_time_slot,
                            is_active=True
                        ).exclude(pk=schedule.id).select_related('course', 'teacher', 'room', 'room__floor')

                        conflict = None
                        if intended_credit <= 2:
                            for es in existing_schedules:
                                if es.course.credit_hours <= 2:
                                    conflict = es
                                    break
                        else:
                            for es in existing_schedules:
                                if es.course.credit_hours >= 3:
                                    conflict = es
                                    break

                    if conflict:
                        return JsonResponse({
                            'success': False,
                            'error': 'این زمان برای این دسته واحدی پر است.',
                            'conflict': {
                                'id': conflict.id,
                                'course_code': conflict.course.course_code,
                                'course_name': conflict.course.course_name,
                                'teacher_name': conflict.teacher.full_name if conflict.teacher else '',
                                'room': conflict.room.room_number,
                                'floor': conflict.room.floor.floor_number,
                                'time_slot': conflict.time_slot,
                                'credit_hours': conflict.course.credit_hours,
                                'semester': conflict.semester,
                                'academic_year': conflict.academic_year,
                                'notes': conflict.notes or ''
                            }
                        })

                    schedule.teacher_id = teacher_id
                    # Allow swapping course too if provided
                    if course_id:
                        schedule.course_id = course_id
                    if room_id:
                        schedule.room_id = room_id
                    if day_of_week:
                        schedule.day_of_week = day_of_week
                    
                    # Update time fields - prefer new fields over legacy
                    if start_time and end_time:
                        from datetime import time
                        schedule.start_time = time.fromisoformat(start_time)
                        schedule.end_time = time.fromisoformat(end_time)
                        # Auto-populate time_slot if it matches a predefined choice
                        time_slot_value = f"{start_time}-{end_time}"
                        if time_slot_value in [choice[0] for choice in ClassSchedule.TIME_CHOICES]:
                            schedule.time_slot = time_slot_value
                    elif time_slot:
                        schedule.time_slot = time_slot
                    
                    schedule.semester = semester
                    schedule.academic_year = academic_year
                    schedule.is_holding = is_holding
                    schedule.notes = notes
                    schedule.save()
                else:
                    # Check if time slot is full for new schedule
                    course = Course.objects.get(id=course_id)
                    credit_hours = course.credit_hours
                    
                    # Check existing schedules for the same time slot and credit hours
                    existing_schedules = ClassSchedule.objects.filter(
                        room_id=room_id,
                        day_of_week=day_of_week,
                        time_slot=time_slot,
                        is_active=True
                    ).select_related('course')
                    
                    # Count schedules by credit hours
                    two_or_less_count = 0
                    three_or_more_count = 0
                    
                    for existing_schedule in existing_schedules:
                        if existing_schedule.course.credit_hours <= 2:
                            two_or_less_count += 1
                        else:
                            three_or_more_count += 1
                    
                    # Check if the slot is full based on credit hours and return conflict details
                    if credit_hours <= 2 and two_or_less_count >= 1:
                        # Find the conflicting schedule for details
                        conflict = None
                        for es in existing_schedules:
                            if es.course.credit_hours <= 2:
                                conflict = es
                                break
                        conflict_payload = None
                        if conflict:
                            conflict_payload = {
                                'id': conflict.id,
                                'course_code': conflict.course.course_code,
                                'course_name': conflict.course.course_name,
                                'teacher_name': conflict.teacher.full_name if conflict.teacher else '',
                                'room': conflict.room.room_number,
                                'floor': conflict.room.floor.floor_number,
                                'time_slot': conflict.time_slot,
                                'credit_hours': conflict.course.credit_hours,
                                'semester': conflict.semester,
                                'academic_year': conflict.academic_year,
                                'notes': conflict.notes or ''
                            }
                        return JsonResponse({
                            'success': False,
                            'error': 'این زمان برای کلاس‌های ≤2 واحدی پر است.',
                            'conflict': conflict_payload
                        })
                    elif credit_hours >= 3 and three_or_more_count >= 1:
                        conflict = None
                        for es in existing_schedules:
                            if es.course.credit_hours >= 3:
                                conflict = es
                                break
                        conflict_payload = None
                        if conflict:
                            conflict_payload = {
                                'id': conflict.id,
                                'course_code': conflict.course.course_code,
                                'course_name': conflict.course.course_name,
                                'teacher_name': conflict.teacher.full_name if conflict.teacher else '',
                                'room': conflict.room.room_number,
                                'floor': conflict.room.floor.floor_number,
                                'time_slot': conflict.time_slot,
                                'credit_hours': conflict.course.credit_hours,
                                'semester': conflict.semester,
                                'academic_year': conflict.academic_year,
                                'notes': conflict.notes or ''
                            }
                        return JsonResponse({
                            'success': False,
                            'error': 'این زمان برای کلاس‌های ≥3 واحدی پر است.',
                            'conflict': conflict_payload
                        })
                    
                    # Create new schedule
                    schedule_data = {
                        'room_id': room_id,
                        'day_of_week': day_of_week,
                        'course_id': course_id,
                        'teacher_id': teacher_id,
                        'semester': semester,
                        'academic_year': academic_year,
                        'is_holding': is_holding,
                        'notes': notes,
                        'is_active': True
                    }
                    
                    # Add time fields - prefer new fields over legacy
                    if start_time and end_time:
                        from datetime import time
                        schedule_data['start_time'] = time.fromisoformat(start_time)
                        schedule_data['end_time'] = time.fromisoformat(end_time)
                        # Auto-populate time_slot if it matches a predefined choice
                        time_slot_value = f"{start_time}-{end_time}"
                        if time_slot_value in [choice[0] for choice in ClassSchedule.TIME_CHOICES]:
                            schedule_data['time_slot'] = time_slot_value
                    elif time_slot:
                        schedule_data['time_slot'] = time_slot
                    
                    ClassSchedule.objects.create(**schedule_data)
                
                return JsonResponse({'success': True})
            except Exception as e:
                return JsonResponse({'success': False, 'error': str(e)})
        
        return JsonResponse({'success': False, 'error': 'Invalid request method'})
    
    @csrf_exempt
    def delete_schedule_view(self, request):
        """AJAX view to delete schedule from chart popup."""
        if request.method == 'POST':
            try:
                import json
                data = json.loads(request.body)
                schedule_id = data.get('schedule_id')
                
                if schedule_id:
                    schedule = ClassSchedule.objects.get(id=schedule_id)
                    schedule.delete()
                    return JsonResponse({'success': True})
                else:
                    return JsonResponse({'success': False, 'error': 'Schedule ID required'})
            except Exception as e:
                return JsonResponse({'success': False, 'error': str(e)})
        
        return JsonResponse({'success': False, 'error': 'Invalid request method'})


@admin.register(ClassCancellationVote)
class ClassCancellationVoteAdmin(admin.ModelAdmin):
    """Admin for viewing cancellation votes (class NOT holding)."""
    
    list_display = ['schedule', 'voter_identifier_short', 'ip_address', 'voted_at']
    list_filter = ['voted_at', 'schedule__day_of_week']
    search_fields = ['schedule__course__course_name', 'voter_identifier']
    readonly_fields = ['schedule', 'voter_identifier', 'voted_at', 'ip_address']
    ordering = ['-voted_at']
    list_per_page = 50
    
    def voter_identifier_short(self, obj):
        """Display shortened voter identifier"""
        return f"{obj.voter_identifier[:16]}..."
    voter_identifier_short.short_description = 'شناسه رای‌دهنده'
    
    def has_add_permission(self, request):
        """Prevent manual addition of votes."""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Make votes read-only."""
        return False


@admin.register(ClassConfirmationVote)
class ClassConfirmationVoteAdmin(admin.ModelAdmin):
    """Admin for viewing confirmation votes (class WILL hold)."""
    
    list_display = ['schedule', 'voter_identifier_short', 'ip_address', 'voted_at']
    list_filter = ['voted_at', 'schedule__day_of_week']
    search_fields = ['schedule__course__course_name', 'voter_identifier']
    readonly_fields = ['schedule', 'voter_identifier', 'voted_at', 'ip_address']
    ordering = ['-voted_at']
    list_per_page = 50
    
    def voter_identifier_short(self, obj):
        """Display shortened voter identifier"""
        return f"{obj.voter_identifier[:16]}..."
    voter_identifier_short.short_description = 'شناسه رای‌دهنده'
    
    def has_add_permission(self, request):
        """Prevent manual addition of votes."""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Make votes read-only."""
        return False


# Customize admin site
admin.site.site_header = 'دانشگاه آزاد اسلامی واحد کرج - پنل مدیریت'
admin.site.site_title = 'مدیریت کلاس‌ها'
admin.site.index_title = 'خوش آمدید به پنل مدیریت'


@admin.register(ImportJob)
class ImportJobAdmin(admin.ModelAdmin):
    list_display = ['faculty', 'semester', 'academic_year', 'source_filename', 'total', 'inserted', 'updated', 'errors_count', 'dry_run', 'status', 'created_at']
    list_filter = ['faculty', 'semester', 'academic_year', 'dry_run', 'status']
    search_fields = ['source_filename']
    readonly_fields = ['faculty', 'semester', 'academic_year', 'source_filename', 'total', 'inserted', 'updated', 'errors_json', 'dry_run', 'status', 'created_at']
    ordering = ['-created_at']
    
    def errors_count(self, obj):
        if obj.errors_json:
            count = len(obj.errors_json)
            return format_html(
                '<span style="color: red; font-weight: bold;">{} خطا</span>',
                count
            )
        return format_html('<span style="color: green;">بدون خطا</span>')
    errors_count.short_description = "تعداد خطاها"
