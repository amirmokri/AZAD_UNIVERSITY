"""
Management command to check and fix faculty assignments.

This command helps ensure data integrity by:
- Identifying courses without faculty assignments
- Showing schedules that might be affected
- Providing statistics per faculty
"""

from django.core.management.base import BaseCommand
from django.db.models import Count
from classes.models import Faculty, Course, ClassSchedule


class Command(BaseCommand):
    help = 'Check faculty assignments and show statistics'

    def add_arguments(self, parser):
        parser.add_argument(
            '--fix',
            action='store_true',
            help='Automatically assign default faculty to courses without one',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=== Faculty Assignment Check ===\n'))

        # Check courses without faculty
        courses_without_faculty = Course.objects.filter(faculty__isnull=True, is_active=True)
        
        if courses_without_faculty.exists():
            self.stdout.write(self.style.WARNING(
                f'\n⚠️  Found {courses_without_faculty.count()} courses WITHOUT faculty:\n'
            ))
            for course in courses_without_faculty:
                schedule_count = course.schedules.filter(is_active=True).count()
                self.stdout.write(
                    f'   - {course.course_code}: {course.course_name} '
                    f'({schedule_count} active schedules)'
                )
            
            if options['fix']:
                # Try to assign a default faculty
                default_faculty = Faculty.objects.filter(is_active=True).first()
                if default_faculty:
                    courses_without_faculty.update(faculty=default_faculty)
                    self.stdout.write(self.style.SUCCESS(
                        f'\n✓ Assigned all courses to: {default_faculty.faculty_name}'
                    ))
                else:
                    self.stdout.write(self.style.ERROR(
                        '\n✗ No active faculty found to assign!'
                    ))
        else:
            self.stdout.write(self.style.SUCCESS('✓ All active courses have faculty assignments\n'))

        # Show statistics per faculty
        self.stdout.write(self.style.SUCCESS('\n=== Faculty Statistics ===\n'))
        
        faculties = Faculty.objects.filter(is_active=True).annotate(
            course_count=Count('courses', filter=models.Q(courses__is_active=True))
        )
        
        for faculty in faculties:
            # Count schedules
            schedule_count = ClassSchedule.objects.filter(
                course__faculty=faculty,
                is_active=True
            ).count()
            
            # Count by day
            schedules_by_day = ClassSchedule.objects.filter(
                course__faculty=faculty,
                is_active=True
            ).values('day_of_week').annotate(count=Count('id'))
            
            self.stdout.write(f'\n📚 {faculty.faculty_name} (کد: {faculty.faculty_code})')
            self.stdout.write(f'   - دروس: {faculty.course_count}')
            self.stdout.write(f'   - کلاس‌های فعال: {schedule_count}')
            
            if schedules_by_day:
                self.stdout.write('   - توزیع روزهای هفته:')
                day_names = {
                    'saturday': 'شنبه',
                    'sunday': 'یکشنبه',
                    'monday': 'دوشنبه',
                    'tuesday': 'سه‌شنبه',
                    'wednesday': 'چهارشنبه',
                    'thursday': 'پنجشنبه',
                    'friday': 'جمعه',
                }
                for day_data in schedules_by_day:
                    day_name = day_names.get(day_data['day_of_week'], day_data['day_of_week'])
                    self.stdout.write(f'     • {day_name}: {day_data["count"]} کلاس')

        # Check for schedule conflicts
        self.stdout.write(self.style.SUCCESS('\n\n=== Checking for Conflicts ===\n'))
        
        conflicts = []
        schedules = ClassSchedule.objects.filter(is_active=True).select_related(
            'course', 'course__faculty', 'room', 'teacher'
        )
        
        checked = set()
        for schedule in schedules:
            key = (schedule.room_id, schedule.day_of_week, schedule.time_slot)
            if key in checked:
                # Found a conflict
                conflicting = ClassSchedule.objects.filter(
                    room=schedule.room,
                    day_of_week=schedule.day_of_week,
                    time_slot=schedule.time_slot,
                    is_active=True
                ).select_related('course', 'course__faculty')
                
                if conflicting.count() > 1:
                    conflicts.append({
                        'room': schedule.room,
                        'day': schedule.day_of_week,
                        'time': schedule.time_slot,
                        'schedules': list(conflicting)
                    })
            checked.add(key)
        
        if conflicts:
            self.stdout.write(self.style.WARNING(
                f'⚠️  Found {len(conflicts)} room conflicts:\n'
            ))
            for conflict in conflicts[:5]:  # Show first 5
                self.stdout.write(
                    f'   - Room {conflict["room"].room_number} on '
                    f'{conflict["day"]} at {conflict["time"]}:'
                )
                for sched in conflict['schedules']:
                    faculty_name = sched.course.faculty.faculty_name if sched.course.faculty else 'بدون دانشکده'
                    self.stdout.write(
                        f'     • {sched.course.course_name} ({faculty_name})'
                    )
        else:
            self.stdout.write(self.style.SUCCESS('✓ No room conflicts found\n'))

        self.stdout.write(self.style.SUCCESS('\n=== Check Complete ===\n'))


# Import models for query
from django.db import models

