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
from django.shortcuts import render, redirect
from django.db import models
from django.db.models import Q, Min, Max, Sum
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.utils.timezone import localtime
from datetime import time, timedelta, datetime
from math import ceil
import logging
from .models import Faculty, Teacher, Course, Floor, Room, ClassSchedule, ImportJob, Ad, AdTracking, FacultyAdminProfile, ScheduleFlag

# Set up logging
logger = logging.getLogger(__name__)

# Chart configuration constants
SLOT_MINUTES = 15  # the base grid resolution
DURATION_PATTERNS = [
    {"label": "105 دقیقه", "minutes": 105},
    {"label": "150 دقیقه", "minutes": 150},
]
DEFAULT_DAY_START = time(8, 0)   # fallback if no classes exist
DEFAULT_DAY_SPAN_HOURS = 12      # fallback

# ------- CONFIG -------
TIME_STEP_MIN = 15                 # 15-minute grid
BAND_A_MIN = 105                   # ≤2 credits (e.g., 8:00→9:45)
BAND_B_MIN = 150                   # ≥3 credits (e.g., 8:00→10:30)
DISPLAY_PADDING_SLOTS = 2          # add some empty columns left/right for breathing room
DAY_DEFAULT_START = time(8, 0)
DAY_DEFAULT_END   = time(19, 0)    # fallback if no classes
# ----------------------

def _to_minutes(t: time) -> int:
    return t.hour * 60 + t.minute

def _from_minutes(m: int) -> time:
    return time(m // 60, m % 60)

def _fmt_hhmm(m: int) -> str:
    hh = m // 60
    mm = m % 60
    return f"{hh:02d}:{mm:02d}"

def _ceil_to_slot(m: int, slot: int) -> int:
    return ((m + slot - 1) // slot) * slot

def _floor_to_slot(m: int, slot: int) -> int:
    return (m // slot) * slot

def _round_down_to_step(dt: time, step=TIME_STEP_MIN) -> time:
    mins = dt.hour * 60 + dt.minute
    mins -= mins % step
    return time(mins // 60, mins % 60)

def _round_up_to_step(dt: time, step=TIME_STEP_MIN) -> time:
    mins = dt.hour * 60 + dt.minute
    if mins % step:
        mins += (step - mins % step)
    return time(mins // 60, mins % 60)

def _time_to_minutes(t: time) -> int:
    return t.hour * 60 + t.minute

def _minutes_to_time(m: int) -> time:
    return time(m // 60, m % 60)

def _time_range_to_slots(t0: time, t1: time, step=TIME_STEP_MIN):
    start_m = _time_to_minutes(t0)
    end_m = _time_to_minutes(t1)
    return [ _minutes_to_time(m) for m in range(start_m, end_m, step) ]

def build_day_bounds(qs, slot_minutes=SLOT_MINUTES):
    """Find earliest start and latest end, expand to slot boundaries."""
    agg = qs.aggregate(min_start=Min("start_time"), max_end=Max("end_time"))
    if not agg["min_start"] or not agg["max_end"]:
        start_min = _to_minutes(DEFAULT_DAY_START)
        end_min = start_min + DEFAULT_DAY_SPAN_HOURS * 60
    else:
        start_min = _to_minutes(agg["min_start"])
        end_min = _to_minutes(agg["max_end"])
        # If a class ends exactly at boundary it's fine; expand a little for nicer margin
        end_min += 5

    start_min = _floor_to_slot(start_min, slot_minutes)
    end_min = _ceil_to_slot(end_min, slot_minutes)
    return start_min, end_min

def build_segments(min_start, max_end, duration_minutes, slot_minutes=SLOT_MINUTES):
    """Build contiguous segments (for the header bands) covering [min_start, max_end)."""
    segs = []
    cur = min_start
    while cur < max_end:
        nxt = min(cur + duration_minutes, max_end)
        span_slots = ceil((nxt - cur) / slot_minutes)
        segs.append({
            "start_min": cur,
            "end_min": nxt,
            "label": f"{_fmt_hhmm(cur)}–{_fmt_hhmm(nxt)}",
            "span_slots": span_slots,
        })
        cur = nxt
    return segs

def class_to_block(s, min_start, slot_minutes=SLOT_MINUTES):
    """Convert a ClassSchedule instance to a grid block."""
    s_min = _to_minutes(s.start_time)
    e_min = _to_minutes(s.end_time)
    start_col = int((s_min - min_start) / slot_minutes) + 2  # +1 for 1-based grid, +1 for room label column
    span_cols = max(1, ceil((e_min - s_min) / slot_minutes))
    return {
        "id": s.id,
        "course_code": getattr(s.course, "course_code", ""),
        "course_name": getattr(s.course, "course_name", ""),
        "teacher_name": getattr(s.teacher, "full_name", ""),
        "semester": getattr(s, "semester", "") or "",
        "credit_hours": getattr(s.course, "credit_hours", ""),
        "is_holding": getattr(s, "is_holding", True),
        "notes": getattr(s, "notes", "") or "",
        "start_hhmm": _fmt_hhmm(s_min),
        "end_hhmm": _fmt_hhmm(e_min),
        "start_col": start_col,
        "span_cols": span_cols,
    }

class FacultyScopedAdminMixin:
    """
    Scope admin querysets and foreign key choices by the user's faculty.
    Superusers are unrestricted; staff with a FacultyAdminProfile are restricted.
    """

    faculty_fk_names = ("faculty",)

    def _get_user_faculty(self, request):
        if request.user.is_superuser:
            return None
        try:
            profile = getattr(request.user, "faculty_admin_profile", None)
            if profile and profile.is_active and profile.faculty:
                return profile.faculty
        except Exception:
            return None
        return None

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        user_faculty = self._get_user_faculty(request)
        if not user_faculty:
            return qs
        model = self.model
        for fk_name in self.faculty_fk_names:
            if hasattr(model, fk_name):
                return qs.filter(**{f"{fk_name}": user_faculty})
        # Fallbacks for models without direct faculty FK
        if model is ClassSchedule:
            return qs.filter(Q(course__faculty=user_faculty) | Q(room__floor__faculty=user_faculty))
        if model is Room:
            return qs.filter(Q(faculty=user_faculty) | Q(floor__faculty=user_faculty))
        if model is Floor:
            return qs.filter(faculty=user_faculty)
        if model is ImportJob:
            return qs.filter(faculty=user_faculty)
        return qs

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        user_faculty = self._get_user_faculty(request)
        if user_faculty and db_field.name == "faculty":
            kwargs["queryset"] = Faculty.objects.filter(pk=user_faculty.pk)
        if user_faculty and db_field.name == "course":
            kwargs["queryset"] = Course.objects.filter(faculty=user_faculty, is_active=True)
        if user_faculty and db_field.name == "teacher":
            kwargs["queryset"] = Teacher.objects.filter(faculty=user_faculty, is_active=True)
        if user_faculty and db_field.name == "floor":
            kwargs["queryset"] = Floor.objects.filter(faculty=user_faculty, is_active=True)
        if user_faculty and db_field.name == "room":
            kwargs["queryset"] = Room.objects.filter(Q(faculty=user_faculty) | Q(floor__faculty=user_faculty), is_active=True)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def save_model(self, request, obj, form, change):
        user_faculty = self._get_user_faculty(request)
        if user_faculty and hasattr(obj, "faculty") and obj.faculty is None:
            obj.faculty = user_faculty
        return super().save_model(request, obj, form, change)

    # Hide faculty field and faculty list filters for scoped users
    def get_fieldsets(self, request, obj=None):
        fieldsets = super().get_fieldsets(request, obj)
        user_faculty = self._get_user_faculty(request)
        if not user_faculty:
            return fieldsets
        # Remove any 'faculty' field from fieldsets for scoped users
        new_fieldsets = []
        for title, opts in fieldsets:
            fields = list(opts.get('fields', ()))
            if 'faculty' in fields:
                fields = [f for f in fields if f != 'faculty']
            new_opts = dict(opts)
            new_opts['fields'] = tuple(fields)
            new_fieldsets.append((title, new_opts))
        return tuple(new_fieldsets)

    def get_list_filter(self, request):
        filters = list(super().get_list_filter(request))
        user_faculty = self._get_user_faculty(request)
        if not user_faculty:
            return filters
        # Remove faculty-based filters for scoped users
        blocked = { 'faculty', 'course__faculty', 'room__faculty' }
        return [f for f in filters if (getattr(f, 'parameter_name', f) not in blocked)]

    # By default, allow scoped users to see the model in admin index
    allow_for_scoped = True

    def get_model_perms(self, request):
        perms = super().get_model_perms(request)
        user_faculty = self._get_user_faculty(request)
        if user_faculty and not getattr(self, 'allow_for_scoped', True):
            # Hide model completely for scoped users
            return {}
        return perms


@admin.register(Faculty)
class FacultyAdmin(FacultyScopedAdminMixin, admin.ModelAdmin):
    allow_for_scoped = False  # Scoped users should not see/manage faculties
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
class TeacherAdmin(FacultyScopedAdminMixin, admin.ModelAdmin):
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
class CourseAdmin(FacultyScopedAdminMixin, admin.ModelAdmin):
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
class FloorAdmin(FacultyScopedAdminMixin, admin.ModelAdmin):
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
class RoomAdmin(FacultyScopedAdminMixin, admin.ModelAdmin):
    """
    Admin configuration for Room model.
    Comprehensive room management with floor filtering.
    """
    
    list_display = ['room_number', 'floor', 'faculty_badge', 'room_type_display', 'position_display', 'schedule_count', 'is_active_badge']
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
            'fields': ('position',)
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
class ClassScheduleAdmin(FacultyScopedAdminMixin, admin.ModelAdmin):
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
            # PDF and PNG export URLs
            path('chart/export-pdf-client/', self.admin_site.admin_view(self.chart_export_pdf_client), name='classes_classschedule_chart_export_pdf_client'),
            path('chart/export-png-client/', self.admin_site.admin_view(self.chart_export_png_client), name='classes_classschedule_chart_export_png_client'),
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
            def __init__(self, *args, **kwargs):
                self._request = kwargs.pop('request', None)
                super().__init__(*args, **kwargs)
                # For scoped users, hide the faculty field entirely and auto-assign
                if self._request and not self._request.user.is_superuser:
                    profile = getattr(self._request.user, 'faculty_admin_profile', None)
                    if profile and profile.faculty:
                        self.fields['faculty'] = forms.ModelChoiceField(
                            queryset=Faculty.objects.filter(pk=profile.faculty.pk, is_active=True),
                            initial=profile.faculty,
                            widget=forms.HiddenInput(),
                            required=True,
                            label='دانشکده'
                        )
                    else:
                        self.fields['faculty'] = forms.ModelChoiceField(
                            queryset=Faculty.objects.none(), required=True, widget=forms.HiddenInput(), label='دانشکده'
                        )
                else:
                    self.fields['faculty'] = forms.ModelChoiceField(
                        queryset=Faculty.objects.filter(is_active=True), label='دانشکده', required=True
                    )

            faculty = forms.ModelChoiceField(queryset=Faculty.objects.none(), label='دانشکده', required=True)
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
            form = ImportForm(request.POST, request.FILES, request=request)
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
            form = ImportForm(request=request)

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
        return obj.room
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
        """Display holding status"""
        if obj.is_holding:
            return format_html('<span style="color: green;">✅ برگزار می‌شود</span>')
        return format_html('<span style="color: orange;">⏸️ برگزار نمی‌شود</span>')
    is_holding_badge.short_description = 'وضعیت برگزاری'
    
    
    def is_active_badge(self, obj):
        """Display active status as colored badge"""
        if obj.is_active:
            return format_html('<span style="color: green;">✓ فعال</span>')
        return format_html('<span style="color: red;">✗ غیرفعال</span>')
    is_active_badge.short_description = 'وضعیت'
    
    def chart_view(self, request, day=None, floor=None):
        """
        Display schedule as a timeline grid with 15-minute slots.
        
        Args:
            request: HTTP request
            day: Day of week filter (optional)
            floor: Floor number filter (optional)
        """
        # Filter base queryset
        qs = ClassSchedule.objects.select_related('course', 'teacher', 'room', 'room__floor')
        user_faculty = self._get_user_faculty(request)
        if user_faculty:
            qs = qs.filter(Q(course__faculty=user_faculty) | Q(room__floor__faculty=user_faculty))
        if day:
            qs = qs.filter(day_of_week=day)
        if floor:
            qs = qs.filter(room__floor__floor_number=floor)

        # Derive day window
        agg = qs.aggregate(min_start=Min('start_time'), max_end=Max('end_time'))
        day_start = agg['min_start'] or DAY_DEFAULT_START
        day_end   = agg['max_end'] or DAY_DEFAULT_END

        # round to grid and add padding
        day_start = _round_down_to_step(day_start)
        day_end   = _round_up_to_step(day_end)
        day_start_m = max(0, _time_to_minutes(day_start) - DISPLAY_PADDING_SLOTS * TIME_STEP_MIN)
        day_end_m   = min(24*60, _time_to_minutes(day_end) + DISPLAY_PADDING_SLOTS * TIME_STEP_MIN)
        day_start, day_end = _minutes_to_time(day_start_m), _minutes_to_time(day_end_m)

        # build grid slots
        slots = _time_range_to_slots(day_start, day_end, TIME_STEP_MIN)
        total_slots = len(slots)

        # index mapping for quick placement
        slot_index = { f"{t.hour:02d}:{t.minute:02d}": i for i, t in enumerate(slots) }

        def minutes_diff(t0: time, t1: time) -> int:
            return _time_to_minutes(t1) - _time_to_minutes(t0)

        # Build room list - show ALL rooms on the selected floor
        if floor:
            rooms_qs = Room.objects.select_related('floor').filter(floor__floor_number=floor, is_active=True)
            if user_faculty:
                rooms_qs = rooms_qs.filter(Q(faculty=user_faculty) | Q(floor__faculty=user_faculty))
            rooms = rooms_qs.order_by('floor__floor_number', 'room_number')
        else:
            # If no floor selected, show all rooms that have schedules for the day
            rooms = (Room.objects.select_related('floor')
                     .filter(schedules__in=qs, is_active=True)
                     .distinct()
                     .order_by('floor__floor_number', 'room_number'))

        # Place schedules on the grid
        per_room_blocks = {}  # room_id -> list of blocks
        for room in rooms:
            per_room_blocks[room.id] = []

        for sch in qs:
            # Skip schedules without proper time data
            if not sch.start_time or not sch.end_time:
                logger.warning(f"Skipping schedule {sch.id} - missing start_time or end_time")
                continue
                
            s = f"{sch.start_time.hour:02d}:{sch.start_time.minute:02d}"
            e = f"{sch.end_time.hour:02d}:{sch.end_time.minute:02d}"
            if s not in slot_index:
                # if outside padding (rare), clamp to grid start
                start_idx = 0
                logger.warning(f"Schedule {sch.id} start time {s} outside grid window, clamping to start")
            else:
                start_idx = slot_index[s]
            duration_min = minutes_diff(sch.start_time, sch.end_time)
            span = max(1, ceil(duration_min / TIME_STEP_MIN))
            band = 'A' if duration_min <= BAND_A_MIN else 'B'  # which header rail it logically belongs to

            per_room_blocks[sch.room_id].append({
                "start_idx": start_idx,        # column index (0-based) within the time grid
                "span": span,                  # how many 15-min columns to span
                "band": band,                  # A (≤105) or B (≥150)
                "id": sch.id,
                "course_code": sch.course.course_code,
                "course_name": sch.course.course_name,
                "teacher_name": sch.teacher.full_name,
                "semester": sch.semester or "",
                "credit_hours": sch.course.credit_hours,
                "is_holding": sch.is_holding,
                "start_label": s,
                "end_label": e,
                "notes": sch.notes or "",
                "academic_year": sch.academic_year or "",
                "room_number": sch.room.room_number,
                "floor_number": sch.room.floor.floor_number,
            })

        # Build the two band rails (top two sticky rows)
        # Repeat BAND_A_MIN and BAND_B_MIN windows across the whole day, aligned with the grid
        def build_band_windows(band_minutes: int):
            windows = []
            anchor_m = _time_to_minutes(day_start)
            end_m = _time_to_minutes(day_end)
            # Step forward by that band length
            while anchor_m < end_m:
                win_start_m = anchor_m
                win_end_m = min(end_m, anchor_m + band_minutes)
                start_idx = (win_start_m - _time_to_minutes(day_start)) // TIME_STEP_MIN
                span = max(1, ceil((win_end_m - win_start_m) / TIME_STEP_MIN))
                windows.append({
                    "start_idx": start_idx,
                    "span": span,
                    "label": f"{_minutes_to_time(win_start_m).strftime('%H:%M')}–{_minutes_to_time(win_end_m).strftime('%H:%M')}"
                })
                anchor_m += band_minutes
            return windows

        band_a_windows = build_band_windows(BAND_A_MIN)
        band_b_windows = build_band_windows(BAND_B_MIN)

        # Get courses and teachers for modal dropdowns
        if user_faculty:
            courses = Course.objects.filter(is_active=True, faculty=user_faculty).select_related('faculty')
            teachers = Teacher.objects.filter(is_active=True, faculty=user_faculty).select_related('faculty')
        else:
            courses = Course.objects.filter(is_active=True).select_related('faculty')
            teachers = Teacher.objects.filter(is_active=True).select_related('faculty')

        # Debug logging
        logger.info(f"Grid view - Day: {day}, Floor: {floor}")
        logger.info(f"Total schedules found: {qs.count()}")
        logger.info(f"Total rooms found: {rooms.count()}")
        logger.info(f"Total slots: {total_slots}")
        logger.info(f"Rooms with schedules: {len([r for r in per_room_blocks.values() if r])}")

        ctx = {
            "title": "Class Timeline",
            "selected_day": day,
            "selected_floor": floor,
            "rooms": rooms,
            "slots": [t.strftime("%H:%M") for t in slots],
            "total_slots": total_slots,
            "per_room_blocks": per_room_blocks,
            "band_a_windows": band_a_windows,  # ≤2 credits rail
            "band_b_windows": band_b_windows,  # ≥3 credits rail
            "time_step": TIME_STEP_MIN,
            "courses": courses,
            "teachers": teachers,
        }
        return render(request, "admin/classes/schedule_grid.html", ctx)
    
    def chart_export_pdf_client(self, request):
        """Export chart as PDF using client-side rendering."""
        return self.chart_view(request)

    def chart_export_png_client(self, request):
        """Export chart as PNG using client-side rendering."""
        return self.chart_view(request)
    
    def day_selection_view(self, request):
        """
        Day selection view for chart with class statistics.
        """
        days = ClassSchedule.DAY_CHOICES
        day_stats = []
        
        # Get statistics for each day
        for day_value, day_name in days:
            user_faculty = self._get_user_faculty(request)
            base_qs = ClassSchedule.objects.filter(day_of_week=day_value, is_active=True)
            if user_faculty:
                base_qs = base_qs.filter(Q(course__faculty=user_faculty) | Q(room__floor__faculty=user_faculty))
            schedules_count = base_qs.count()

            active_qs = base_qs.filter(is_holding=True)
            active_schedules_count = active_qs.count()

            if user_faculty:
                rooms_count = Room.objects.filter(
                    is_active=True,
                    schedules__day_of_week=day_value,
                    schedules__is_active=True,
                ).filter(Q(faculty=user_faculty) | Q(floor__faculty=user_faculty)).distinct().count()
            else:
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
            user_faculty = self._get_user_faculty(request)
            if user_faculty:
                floors = Floor.objects.filter(
                    is_active=True,
                    faculty=user_faculty,
                    rooms__schedules__day_of_week=day,
                    rooms__schedules__is_active=True,
                ).distinct().order_by('floor_number')
            else:
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
                user_faculty = self._get_user_faculty(request)
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

                # Faculty scope validation of provided FKs
                if user_faculty:
                    if course_id and not Course.objects.filter(id=course_id, faculty=user_faculty, is_active=True).exists():
                        return JsonResponse({'success': False, 'error': 'دسترسی به این درس مجاز نیست'}, status=403)
                    if teacher_id and not Teacher.objects.filter(id=teacher_id, faculty=user_faculty, is_active=True).exists():
                        return JsonResponse({'success': False, 'error': 'دسترسی به این استاد مجاز نیست'}, status=403)
                    if room_id and not Room.objects.filter(is_active=True).filter(Q(id=room_id) & (Q(faculty=user_faculty) | Q(floor__faculty=user_faculty))).exists():
                        return JsonResponse({'success': False, 'error': 'دسترسی به این اتاق مجاز نیست'}, status=403)

                if schedule_id:
                    # Update existing schedule with conflict check
                    if user_faculty:
                        schedule = ClassSchedule.objects.filter(
                            Q(id=schedule_id) & (Q(course__faculty=user_faculty) | Q(room__floor__faculty=user_faculty))
                        ).first()
                        if not schedule:
                            return JsonResponse({'success': False, 'error': 'دسترسی به این برنامه مجاز نیست'}, status=403)
                    else:
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
                    user_faculty = self._get_user_faculty(request)
                    if user_faculty:
                        schedule = ClassSchedule.objects.filter(
                            Q(id=schedule_id) & (Q(course__faculty=user_faculty) | Q(room__floor__faculty=user_faculty))
                        ).first()
                        if not schedule:
                            return JsonResponse({'success': False, 'error': 'دسترسی به این برنامه مجاز نیست'}, status=403)
                    else:
                        schedule = ClassSchedule.objects.get(id=schedule_id)
                    schedule.delete()
                    return JsonResponse({'success': True})
                else:
                    return JsonResponse({'success': False, 'error': 'Schedule ID required'})
            except Exception as e:
                return JsonResponse({'success': False, 'error': str(e)})
        
        return JsonResponse({'success': False, 'error': 'Invalid request method'})




# Customize admin site
admin.site.site_header = 'دانشگاه آزاد اسلامی واحد کرج - پنل مدیریت'
admin.site.site_title = 'مدیریت کلاس‌ها'
admin.site.index_title = 'خوش آمدید به پنل مدیریت'


@admin.register(ImportJob)
class ImportJobAdmin(FacultyScopedAdminMixin, admin.ModelAdmin):
    allow_for_scoped = False  # Hide import logs for faculty-admins; principal only
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


@admin.register(Ad)
class AdAdmin(admin.ModelAdmin):
    allow_for_scoped = False  # Principal only
    """Admin interface for Ad model."""
    
    list_display = ['name', 'is_active', 'priority', 'start_at', 'end_at', 'created_at', 'impressions_count', 'clicks_count', 'ctr']
    list_filter = ['is_active', 'created_at', 'start_at', 'end_at']
    search_fields = ['name', 'link']
    readonly_fields = ['created_at', 'updated_at', 'image_preview']
    
    fieldsets = (
        ('اطلاعات اصلی', {
            'fields': ('name', 'image', 'image_preview', 'link')
        }),
        ('تنظیمات نمایش', {
            'fields': ('is_active', 'priority', 'start_at', 'end_at')
        }),
        ('اطلاعات سیستم', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def image_preview(self, obj):
        """Display image preview in admin."""
        if obj.image:
            return format_html(
                '<img src="{}" style="max-width: 300px; max-height: 200px; border-radius: 8px;" />',
                obj.image.url
            )
        return format_html('<span style="color: #999;">هیچ تصویری بارگذاری نشده</span>')
    image_preview.short_description = "پیش‌نمایش تصویر"
    
    def impressions_count(self, obj):
        """Display total impressions."""
        total = AdTracking.objects.filter(ad=obj, event_type='impression').aggregate(
            total=models.Sum('count')
        )['total'] or 0
        return format_html('<strong>{}</strong>', total)
    impressions_count.short_description = "تعداد نمایش‌ها"
    
    def clicks_count(self, obj):
        """Display total clicks."""
        total = AdTracking.objects.filter(ad=obj, event_type='click').aggregate(
            total=models.Sum('count')
        )['total'] or 0
        return format_html('<strong>{}</strong>', total)
    clicks_count.short_description = "تعداد کلیک‌ها"
    
    def ctr(self, obj):
        """Display click-through rate."""
        impressions = AdTracking.objects.filter(ad=obj, event_type='impression').aggregate(
            total=models.Sum('count')
        )['total'] or 0
        clicks = AdTracking.objects.filter(ad=obj, event_type='click').aggregate(
            total=models.Sum('count')
        )['total'] or 0
        
        if impressions > 0:
            rate = (clicks / impressions) * 100
            color = 'green' if rate > 2 else 'orange' if rate > 1 else 'red'
            return format_html(
                '<span style="color: {}; font-weight: bold;">{:.2f}%</span>',
                color, rate
            )
        return format_html('<span style="color: #999;">-</span>')
    ctr.short_description = "نرخ کلیک (CTR)"


@admin.register(AdTracking)
class AdTrackingAdmin(admin.ModelAdmin):
    allow_for_scoped = False  # Principal only
    """Admin interface for AdTracking model."""
    
    list_display = ['ad', 'event_type', 'date', 'count', 'updated_at']
    list_filter = ['event_type', 'date', 'ad']
    search_fields = ['ad__name']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'date'
    
    fieldsets = (
        ('اطلاعات ردیابی', {
            'fields': ('ad', 'event_type', 'date', 'count')
        }),
        ('اطلاعات سیستم', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(FacultyAdminProfile)
class FacultyAdminProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'faculty', 'is_active', 'created_at', 'updated_at']
    list_filter = ['is_active', 'faculty']
    search_fields = ['user__username', 'user__email', 'faculty__faculty_name']
    autocomplete_fields = ['user', 'faculty']

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        # Ensure the linked user is staff and has model permissions for scoped admin usage
        try:
            user = obj.user
            if not user.is_superuser:
                if not user.is_staff:
                    user.is_staff = True
                    user.save(update_fields=['is_staff'])

                # Grant add/change/delete/view perms for allowed models
                allowed_models = [Teacher, Course, Floor, Room, ClassSchedule]
                for model in allowed_models:
                    ct = ContentType.objects.get_for_model(model)
                    for action in ['add', 'change', 'delete', 'view']:
                        codename = f"{action}_{model._meta.model_name}"
                        try:
                            perm = Permission.objects.get(content_type=ct, codename=codename)
                            user.user_permissions.add(perm)
                        except Permission.DoesNotExist:
                            continue
        except Exception:
            # Do not break admin save on permission assignment issues
            pass


@admin.register(ScheduleFlag)
class ScheduleFlagAdmin(FacultyScopedAdminMixin, admin.ModelAdmin):
    """Admin for student-reported schedule flags, scoped by faculty.

    Clicking a flag redirects to the related ClassSchedule change page for quick resolution.
    """

    faculty_fk_names = ("faculty",)
    list_display = [
        'id', 'schedule_display', 'reason_badge', 'created_at', 'faculty', 'go_to_schedule'
    ]
    list_filter = ['reason', 'faculty', 'created_at']
    search_fields = ['schedule__course__course_name', 'schedule__teacher__full_name', 'schedule__course__course_code']
    readonly_fields = ['schedule', 'faculty', 'reason', 'description', 'reporter_ip', 'created_at']
    ordering = ['-created_at']
    list_per_page = 50

    fieldsets = (
        ('گزارش', {
            'fields': ('schedule', 'faculty', 'reason', 'description', 'reporter_ip', 'created_at')
        }),
    )

    def schedule_display(self, obj):
        return format_html('<strong>{}</strong><br/><small>{}</small>', obj.schedule.course.course_name, obj.schedule)
    schedule_display.short_description = 'کلاس'

    def reason_badge(self, obj):
        color = '#f44336' if obj.reason == ScheduleFlag.REASON_NOT_HOLDING else '#ff9800'
        return format_html('<span style="background:{};color:#fff;padding:3px 8px;border-radius:8px;font-weight:700;">{}</span>', color, obj.get_reason_display())
    reason_badge.short_description = 'دلیل'

    def has_change_permission(self, request, obj=None):
        # Make flags read-only; handling happens on the schedule page
        return False

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser

    def get_queryset(self, request):
        qs = super().get_queryset(request).select_related('schedule', 'schedule__course', 'schedule__teacher')
        return qs

    def go_to_schedule(self, obj):
        try:
            url = reverse('admin:classes_classschedule_change', args=[obj.schedule_id])
            return format_html('<a class="button" href="{}" style="background:#1976d2;color:#fff;padding:4px 10px;border-radius:6px;">ویرایش کلاس</a>', url)
        except Exception:
            return '-'
    go_to_schedule.short_description = 'اقدام'

