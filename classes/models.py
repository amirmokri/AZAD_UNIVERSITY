"""
Models for the class scheduling and management system.

This module defines the database schema for:
- Teachers: Faculty members who teach courses
- Courses: Academic courses offered
- Floors: Building floors
- Rooms: Physical rooms/classrooms in the building
- ClassSchedules: Schedule entries linking all components

The models are designed for scalability and easy administration.
All models include proper validation, error handling, and Persian language support.
"""

from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator


class Faculty(models.Model):
    """Faculty model representing university faculties/departments."""
    
    faculty_name = models.CharField(max_length=200, unique=True, verbose_name="نام دانشکده")
    faculty_code = models.CharField(max_length=20, unique=True, verbose_name="کد دانشکده")
    faculty_image = models.CharField(max_length=200, blank=True, null=True, verbose_name="نام فایل تصویر", 
                                     help_text="نام فایل تصویر در پوشه static/images/ (مثال: AI.jpg)")
    description = models.TextField(blank=True, null=True, verbose_name="توضیحات")
    is_active = models.BooleanField(default=True, verbose_name="فعال")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ایجاد")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="تاریخ بروزرسانی")
    
    class Meta:
        verbose_name = "دانشکده"
        verbose_name_plural = "دانشکده‌ها"
        ordering = ['faculty_name']
    
    def __str__(self):
        return self.faculty_name
    
    def get_image_url(self):
        """Get the full static URL for the faculty image"""
        if self.faculty_image:
            return f'images/{self.faculty_image}'
        return None


class Teacher(models.Model):
    """Teacher model representing faculty members."""
    
    faculty = models.ForeignKey('Faculty', on_delete=models.CASCADE, related_name='teachers', null=True, blank=True, verbose_name="دانشکده")
    full_name = models.CharField(max_length=200, verbose_name="نام کامل استاد")
    email = models.EmailField(blank=True, null=True, verbose_name="ایمیل")
    phone_number = models.CharField(max_length=20, blank=True, null=True, verbose_name="شماره تماس")
    specialization = models.CharField(max_length=100, blank=True, null=True, verbose_name="تخصص")
    is_active = models.BooleanField(default=True, verbose_name="فعال")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ایجاد")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="تاریخ بروزرسانی")
    
    class Meta:
        verbose_name = "استاد"
        verbose_name_plural = "اساتید"
        ordering = ['faculty', 'full_name']
    
    def __str__(self):
        if self.faculty:
            return f"{self.full_name} ({self.faculty.faculty_name})"
        return self.full_name


class Course(models.Model):
    """Course model representing academic courses."""
    
    faculty = models.ForeignKey('Faculty', on_delete=models.CASCADE, related_name='courses', null=True, blank=True, verbose_name="دانشکده")
    course_code = models.CharField(max_length=20, unique=True, verbose_name="کد درس")
    course_name = models.CharField(max_length=200, verbose_name="نام درس")
    credit_hours = models.PositiveIntegerField(default=3, verbose_name="تعداد واحد")
    description = models.TextField(blank=True, null=True, verbose_name="توضیحات")
    is_active = models.BooleanField(default=True, verbose_name="فعال")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ایجاد")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="تاریخ بروزرسانی")
    
    class Meta:
        verbose_name = "درس"
        verbose_name_plural = "دروس"
        ordering = ['course_code']
    
    def __str__(self):
        return f"{self.course_code} - {self.course_name}"


class Floor(models.Model):
    """Floor model representing building floors."""
    
    faculty = models.ForeignKey('Faculty', on_delete=models.CASCADE, related_name='floors', null=True, blank=True, verbose_name="دانشکده")
    floor_number = models.PositiveIntegerField(verbose_name="شماره طبقه")
    floor_name = models.CharField(max_length=50, verbose_name="نام طبقه")
    description = models.TextField(blank=True, null=True, verbose_name="توضیحات")
    is_active = models.BooleanField(default=True, verbose_name="فعال")
    
    class Meta:
        verbose_name = "طبقه"
        verbose_name_plural = "طبقات"
        ordering = ['faculty', 'floor_number']
        unique_together = ['faculty', 'floor_number']
    
    def __str__(self):
        if self.faculty:
            return f"{self.floor_name} - {self.faculty.faculty_name}"
        return self.floor_name


class Room(models.Model):
    """Room model representing physical rooms and classrooms."""
    
    ROOM_TYPE_CHOICES = [
        ('classroom', 'کلاس درس'),
        ('lab', 'آزمایشگاه'),
        ('office', 'دفتر'),
        ('study_hall', 'سالن مطالعه'),
        ('other', 'سایر'),
    ]
    
    POSITION_CHOICES = [
        ('left', 'سمت چپ راهرو'),
        ('right', 'سمت راست راهرو'),
        ('center', 'وسط راهرو'),
    ]
    
    faculty = models.ForeignKey('Faculty', on_delete=models.CASCADE, related_name='rooms', null=True, blank=True, verbose_name="دانشکده")
    floor = models.ForeignKey(Floor, on_delete=models.CASCADE, related_name='rooms', verbose_name="طبقه")
    room_number = models.CharField(max_length=20, verbose_name="شماره اتاق")
    room_type = models.CharField(max_length=20, choices=ROOM_TYPE_CHOICES, default='classroom', verbose_name="نوع اتاق")
    capacity = models.PositiveIntegerField(verbose_name="ظرفیت")
    position = models.CharField(max_length=10, choices=POSITION_CHOICES, default='left', verbose_name="موقعیت")
    is_active = models.BooleanField(default=True, verbose_name="فعال")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ایجاد")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="تاریخ بروزرسانی")
    
    class Meta:
        verbose_name = "اتاق"
        verbose_name_plural = "اتاق‌ها"
        ordering = ['faculty', 'floor__floor_number', 'room_number']
        unique_together = ['floor', 'room_number']
    
    def __str__(self):
        if self.faculty:
            return f"{self.floor.floor_name} - اتاق {self.room_number} ({self.faculty.faculty_name})"
        return f"{self.floor.floor_name} - اتاق {self.room_number}"
    
    def save(self, *args, **kwargs):
        # Auto-assign faculty from floor if not set
        if not self.faculty and self.floor and self.floor.faculty:
            self.faculty = self.floor.faculty
        super().save(*args, **kwargs)




class ClassSchedule(models.Model):
    """ClassSchedule model linking all components together."""
    
    DAY_CHOICES = [
        ('saturday', 'شنبه'),
        ('sunday', 'یکشنبه'),
        ('monday', 'دوشنبه'),
        ('tuesday', 'سه‌شنبه'),
        ('wednesday', 'چهارشنبه'),
        ('thursday', 'پنجشنبه'),
        ('friday', 'جمعه'),
    ]
    
    # Time slots for courses with 2 or less credit hours
    TIME_CHOICES_2_OR_LESS = [
        ('07:30-09:15', '7:30-9:15'),
        ('09:15-11:00', '9:15-11:00'),
        ('11:00-13:15', '11:00-13:15'),
        ('13:15-15:00', '13:15-15:00'),
        ('15:00-16:45', '15:00-16:45'),
        ('16:45-18:00', '16:45-18:00'),
    ]
    
    # Time slots for courses with 3 or more credit hours
    TIME_CHOICES_3_OR_MORE = [
        ('07:30-10:10', '7:30-10:10'),
        ('10:15-13:30', '10:15-13:30'),
        ('13:30-16:00', '13:30-16:00'),
        ('16:00-18:30', '16:00-18:30'),
    ]
    
    # Combined time choices for backward compatibility
    TIME_CHOICES = TIME_CHOICES_2_OR_LESS + TIME_CHOICES_3_OR_MORE
    
    teacher = models.ForeignKey(Teacher, on_delete=models.SET_NULL, null=True, blank=True, related_name='schedules', verbose_name="استاد")
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='schedules', verbose_name="درس")
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='schedules', verbose_name="اتاق")
    day_of_week = models.CharField(max_length=15, choices=DAY_CHOICES, verbose_name="روز هفته")
    
    # New flexible time fields - primary timing source
    start_time = models.TimeField(
        null=True, 
        blank=True, 
        verbose_name="ساعت شروع",
        help_text="ساعت شروع کلاس (مثال: 07:30)"
    )
    end_time = models.TimeField(
        null=True, 
        blank=True, 
        verbose_name="ساعت پایان",
        help_text="ساعت پایان کلاس (مثال: 09:15)"
    )
    
    # Legacy time slot field - kept for backward compatibility
    time_slot = models.CharField(
        max_length=15, 
        choices=TIME_CHOICES, 
        null=True, 
        blank=True, 
        verbose_name="بازه زمانی (قدیمی)",
        help_text="بازه زمانی قدیمی - به صورت خودکار از ساعت شروع و پایان محاسبه می‌شود"
    )
    
    semester = models.CharField(max_length=20, blank=True, null=True, verbose_name="نیمسال")
    academic_year = models.CharField(max_length=20, blank=True, null=True, verbose_name="سال تحصیلی")
    notes = models.TextField(blank=True, null=True, verbose_name="یادداشت‌ها")
    is_holding = models.BooleanField(
        default=True,
        verbose_name="کلاس برگزار می‌شود",
        help_text="آیا این کلاس در حال حاضر برگزار می‌شود؟"
    )
    is_active = models.BooleanField(default=True, verbose_name="فعال")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ایجاد")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="تاریخ بروزرسانی")
    
    class Meta:
        verbose_name = "برنامه کلاسی"
        verbose_name_plural = "برنامه‌های کلاسی"
        ordering = ['day_of_week', 'start_time', 'room__floor__floor_number']
        unique_together = ['room', 'day_of_week', 'start_time', 'end_time']
    
    def __str__(self):
        day_display = dict(self.DAY_CHOICES).get(self.day_of_week, '')
        teacher_name = self.teacher.full_name if self.teacher else 'بدون استاد'
        time_display = self.get_time_display()
        return f"{day_display} - {time_display} - {self.course.course_name} - {teacher_name}"
    
    def get_time_display(self):
        """
        Get formatted time display, preferring start_time/end_time over time_slot.
        
        Returns:
            str: Formatted time string (e.g., "07:30-09:15" or "07:30-09:15")
        """
        if self.start_time and self.end_time:
            return f"{self.start_time.strftime('%H:%M')}-{self.end_time.strftime('%H:%M')}"
        elif self.time_slot:
            return self.time_slot
        else:
            return "زمان نامشخص"
    
    def get_duration_hours(self):
        """
        Calculate class duration in hours.
        
        Returns:
            float: Duration in hours, or None if times are missing
        """
        if self.start_time and self.end_time:
            from datetime import datetime, timedelta
            start_dt = datetime.combine(datetime.today(), self.start_time)
            end_dt = datetime.combine(datetime.today(), self.end_time)
            
            # Handle case where end_time is next day
            if end_dt <= start_dt:
                end_dt += timedelta(days=1)
            
            duration = end_dt - start_dt
            return duration.total_seconds() / 3600  # Convert to hours
        return None
    
    def is_time_conflict_with(self, other_schedule):
        """
        Check if this schedule conflicts with another schedule.
        
        This method allows classes that end exactly when another starts
        (e.g., 8:00-10:30 and 10:30-12:00) to avoid false conflicts.
        
        Args:
            other_schedule: Another ClassSchedule instance
            
        Returns:
            bool: True if there's a time conflict (overlapping times)
        """
        if not (self.start_time and self.end_time and 
                other_schedule.start_time and other_schedule.end_time):
            return False
        
        # Check if schedules are on the same day
        if self.day_of_week != other_schedule.day_of_week:
            return False
        
        # Check for time overlap
        # Allow classes that end exactly when another starts (e.g., 8:00-10:30 and 10:30-12:00)
        return not (self.end_time < other_schedule.start_time or 
                   other_schedule.end_time < self.start_time)
    
    @classmethod
    def get_time_choices_for_course(cls, course):
        """
        Get appropriate time choices based on course credit hours.
        
        Args:
            course: Course instance
            
        Returns:
            List of time choices appropriate for the course's credit hours
        """
        if course.credit_hours <= 2:
            return cls.TIME_CHOICES_2_OR_LESS
        else:
            return cls.TIME_CHOICES_3_OR_MORE
    
    def get_available_time_choices(self):
        """
        Get available time choices for this schedule's course.
        
        Returns:
            List of time choices appropriate for the course's credit hours
        """
        return self.get_time_choices_for_course(self.course)
    
    def clean(self):
        """
        Validate schedule before saving to prevent conflicts.
        
        Checks for:
        1. Room conflicts (same room can't host overlapping classes)
        2. Teacher conflicts (same teacher can't teach two classes at once)
        3. Time validation and duration warnings
        
        Raises:
            ValidationError: If any conflict is detected with detailed information
        """
        super().clean()
        
        # Skip validation if this is an import operation
        if hasattr(self, '_skip_validation') and self._skip_validation:
            return
        
        # Validate that we have timing information
        if not (self.start_time and self.end_time) and not self.time_slot:
            raise ValidationError({
                'start_time': 'لطفاً ساعت شروع و پایان کلاس را مشخص کنید.',
                'end_time': 'لطفاً ساعت شروع و پایان کلاس را مشخص کنید.'
            })
        
        # Validate time logic
        if self.start_time and self.end_time:
            if self.start_time >= self.end_time:
                raise ValidationError({
                    'end_time': 'ساعت پایان باید بعد از ساعت شروع باشد.'
                })
            
            # Check for reasonable class duration (minimum 30 minutes, maximum 6 hours)
            duration_hours = self.get_duration_hours()
            if duration_hours:
                if duration_hours < 0.5:  # Less than 30 minutes
                    raise ValidationError({
                        'end_time': 'مدت زمان کلاس باید حداقل 30 دقیقه باشد.'
                    })
                elif duration_hours > 6:  # More than 6 hours
                    raise ValidationError({
                        'end_time': 'مدت زمان کلاس نمی‌تواند بیش از 6 ساعت باشد.'
                    })
        
        # Check for room conflicts - CRITICAL: prevent double-booking
        if self.room and self.day_of_week and (self.start_time and self.end_time):
            # Find all schedules for the same room and day
            room_schedules = ClassSchedule.objects.filter(
                room=self.room,
                day_of_week=self.day_of_week,
                is_active=True
            ).exclude(pk=self.pk)
            
            # Check for time conflicts
            for schedule in room_schedules:
                if schedule.start_time and schedule.end_time:
                    if self.is_time_conflict_with(schedule):
                        teacher_name = schedule.teacher.full_name if schedule.teacher else 'نامشخص'
                        day_display = dict(self.DAY_CHOICES).get(self.day_of_week, self.day_of_week)
                        time_display = schedule.get_time_display()
                        error_msg = (
                            f'❌ تداخل زمانی! این اتاق در این بازه زمانی قبلاً رزرو شده است.\n\n'
                            f'📚 درس: {schedule.course.course_name}\n'
                            f'👨‍🏫 استاد: {teacher_name}\n'
                            f'📅 روز: {day_display}\n'
                            f'⏰ ساعت: {time_display}\n\n'
                            f'لطفاً اتاق، روز یا زمان دیگری انتخاب کنید.'
                        )
                        raise ValidationError({'room': error_msg})
        
        # Check for teacher conflicts
        if self.teacher and self.day_of_week and (self.start_time and self.end_time):
            # Find all schedules for the same teacher and day
            teacher_schedules = ClassSchedule.objects.filter(
                teacher=self.teacher,
                day_of_week=self.day_of_week,
                is_active=True
            ).exclude(pk=self.pk)
            
            # Check for time conflicts
            for schedule in teacher_schedules:
                if schedule.start_time and schedule.end_time:
                    if self.is_time_conflict_with(schedule):
                        day_display = dict(self.DAY_CHOICES).get(self.day_of_week, self.day_of_week)
                        time_display = schedule.get_time_display()
                        error_msg = (
                            f'❌ تداخل زمانی! این استاد در این بازه زمانی کلاس دیگری دارد.\n\n'
                            f'📚 درس: {schedule.course.course_name}\n'
                            f'🚪 اتاق: {schedule.room.room_number}\n'
                            f'📅 روز: {day_display}\n'
                            f'⏰ ساعت: {time_display}\n\n'
                            f'لطفاً استاد، روز یا زمان دیگری انتخاب کنید.'
                        )
                        raise ValidationError({'teacher': error_msg})
        
        # Validate duration matches course credit hours (warning, not error)
        if self.course and self.start_time and self.end_time:
            duration_hours = self.get_duration_hours()
            if duration_hours:
                credit_hours = getattr(self.course, 'credit_hours', 0)
                if credit_hours > 0:
                    # Typical durations: 2-unit = 1.5-2h, 3-unit = 2.5-3h
                    expected_min = credit_hours * 0.8  # 80% of credit hours
                    expected_max = credit_hours * 1.2  # 120% of credit hours
                    
                    # Duration validation removed - warnings were cluttering logs
                    # Classes can have flexible durations regardless of credit hours
    
    
    
    
    
    
    
    def save(self, *args, **kwargs):
        """
        Override save to handle time_slot backfill and run validation.
        
        Automatically populates time_slot from start_time/end_time for backward compatibility.
        
        Args:
            skip_validation: If True, skip the validation checks (useful for imports)
        """
        # Backfill time_slot from start_time/end_time if not set
        if self.start_time and self.end_time and not self.time_slot:
            time_slot_value = f"{self.start_time.strftime('%H:%M')}-{self.end_time.strftime('%H:%M')}"
            # Only set if it matches one of the predefined choices
            if time_slot_value in [choice[0] for choice in self.TIME_CHOICES]:
                self.time_slot = time_slot_value
        
        # Skip validation if requested (useful for bulk imports)
        skip_validation = kwargs.pop('skip_validation', False) or getattr(self, '_skip_validation', False)
        if not skip_validation:
            # Run validation
            self.full_clean()
        
        super().save(*args, **kwargs)


class ImportJob(models.Model):
    """Audit log for Excel imports of schedules."""

    STATUS_CHOICES = [
        ("pending", "در انتظار"),
        ("completed", "انجام شد"),
        ("failed", "ناموفق"),
    ]

    faculty = models.ForeignKey(Faculty, on_delete=models.CASCADE, related_name="import_jobs", verbose_name="دانشکده")
    semester = models.CharField(max_length=32, verbose_name="نیمسال")
    academic_year = models.CharField(max_length=32, verbose_name="سال تحصیلی")
    source_filename = models.CharField(max_length=255, verbose_name="نام فایل منبع")
    total = models.PositiveIntegerField(default=0, verbose_name="تعداد کل")
    inserted = models.PositiveIntegerField(default=0, verbose_name="تعداد افزوده‌شده")
    updated = models.PositiveIntegerField(default=0, verbose_name="تعداد بروزرسانی‌شده")
    errors_json = models.JSONField(default=list, blank=True, verbose_name="خطاها")
    dry_run = models.BooleanField(default=True, verbose_name="اجرای آزمایشی")
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default="pending", verbose_name="وضعیت")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="ایجاد شده در")

    class Meta:
        verbose_name = "لاگ درون‌ریزی"
        verbose_name_plural = "لاگ‌های درون‌ریزی"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.faculty} - {self.semester} - {self.academic_year} ({self.status})"
