"""
Comprehensive audit command for faculty data integrity.

This command checks and fixes all faculty assignments across the entire system.
"""

from django.core.management.base import BaseCommand
from django.db import models
from classes.models import Faculty, Course, Teacher, Floor, Room, ClassSchedule


class Command(BaseCommand):
    help = 'Comprehensive audit of all faculty assignments'

    def add_arguments(self, parser):
        parser.add_argument(
            '--fix',
            action='store_true',
            help='Automatically fix issues where possible',
        )
        parser.add_argument(
            '--faculty',
            type=int,
            help='Default faculty ID to assign to items without faculty',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('\n' + '='*70))
        self.stdout.write(self.style.SUCCESS('  COMPREHENSIVE FACULTY DATA AUDIT'))
        self.stdout.write(self.style.SUCCESS('  دانشگاه آزاد اسلامی واحد کرج'))
        self.stdout.write(self.style.SUCCESS('='*70 + '\n'))

        # Get default faculty if specified
        default_faculty = None
        if options['faculty']:
            try:
                default_faculty = Faculty.objects.get(id=options['faculty'])
                self.stdout.write(f"Default Faculty: {default_faculty.faculty_name}\n")
            except Faculty.DoesNotExist:
                self.stdout.write(self.style.ERROR(f"Faculty with ID {options['faculty']} not found!\n"))
                return

        # 1. Check Faculties
        self.stdout.write(self.style.WARNING('\n📚 FACULTIES:\n'))
        faculties = Faculty.objects.all()
        if not faculties.exists():
            self.stdout.write(self.style.ERROR('   ❌ NO FACULTIES FOUND! Please create faculties first.\n'))
            return
        
        for faculty in faculties:
            status = '✓ Active' if faculty.is_active else '✗ Inactive'
            self.stdout.write(f'   {status} - {faculty.faculty_name} (Code: {faculty.faculty_code})')

        # 2. Check Courses
        self.stdout.write(self.style.WARNING('\n\n📖 COURSES:\n'))
        courses_without_faculty = Course.objects.filter(faculty__isnull=True, is_active=True)
        
        if courses_without_faculty.exists():
            self.stdout.write(self.style.ERROR(f'   ⚠️  {courses_without_faculty.count()} courses WITHOUT faculty:\n'))
            for course in courses_without_faculty:
                self.stdout.write(f'      - {course.course_code}: {course.course_name}')
            
            if options['fix'] and default_faculty:
                courses_without_faculty.update(faculty=default_faculty)
                self.stdout.write(self.style.SUCCESS(f'\n   ✓ Assigned {courses_without_faculty.count()} courses to {default_faculty.faculty_name}'))
        else:
            self.stdout.write(self.style.SUCCESS('   ✓ All active courses have faculty assignments'))

        # 3. Check Teachers
        self.stdout.write(self.style.WARNING('\n\n👨‍🏫 TEACHERS:\n'))
        teachers_without_faculty = Teacher.objects.filter(faculty__isnull=True, is_active=True)
        
        if teachers_without_faculty.exists():
            self.stdout.write(self.style.ERROR(f'   ⚠️  {teachers_without_faculty.count()} teachers WITHOUT faculty:\n'))
            for teacher in teachers_without_faculty:
                class_count = teacher.schedules.filter(is_active=True).count()
                self.stdout.write(f'      - {teacher.full_name} ({class_count} classes)')
            
            if options['fix'] and default_faculty:
                teachers_without_faculty.update(faculty=default_faculty)
                self.stdout.write(self.style.SUCCESS(f'\n   ✓ Assigned {teachers_without_faculty.count()} teachers to {default_faculty.faculty_name}'))
        else:
            self.stdout.write(self.style.SUCCESS('   ✓ All active teachers have faculty assignments'))

        # 4. Check Floors
        self.stdout.write(self.style.WARNING('\n\n🏢 FLOORS:\n'))
        floors_without_faculty = Floor.objects.filter(faculty__isnull=True, is_active=True)
        
        if floors_without_faculty.exists():
            self.stdout.write(self.style.ERROR(f'   ⚠️  {floors_without_faculty.count()} floors WITHOUT faculty:\n'))
            for floor in floors_without_faculty:
                room_count = floor.rooms.count()
                self.stdout.write(f'      - {floor.floor_name} (Floor #{floor.floor_number}, {room_count} rooms)')
            
            if options['fix'] and default_faculty:
                floors_without_faculty.update(faculty=default_faculty)
                self.stdout.write(self.style.SUCCESS(f'\n   ✓ Assigned {floors_without_faculty.count()} floors to {default_faculty.faculty_name}'))
        else:
            self.stdout.write(self.style.SUCCESS('   ✓ All active floors have faculty assignments'))

        # 5. Check Rooms
        self.stdout.write(self.style.WARNING('\n\n🚪 ROOMS:\n'))
        rooms_without_faculty = Room.objects.filter(faculty__isnull=True, is_active=True)
        
        if rooms_without_faculty.exists():
            self.stdout.write(self.style.ERROR(f'   ⚠️  {rooms_without_faculty.count()} rooms WITHOUT faculty:\n'))
            for room in rooms_without_faculty[:10]:  # Show first 10
                self.stdout.write(f'      - Room {room.room_number} on {room.floor.floor_name}')
            if rooms_without_faculty.count() > 10:
                self.stdout.write(f'      ... and {rooms_without_faculty.count() - 10} more')
            
            if options['fix']:
                # Auto-fix rooms based on their floor's faculty
                fixed = 0
                for room in rooms_without_faculty:
                    if room.floor and room.floor.faculty:
                        room.faculty = room.floor.faculty
                        room.save()
                        fixed += 1
                    elif default_faculty:
                        room.faculty = default_faculty
                        room.save()
                        fixed += 1
                
                self.stdout.write(self.style.SUCCESS(f'\n   ✓ Fixed {fixed} rooms'))
        else:
            self.stdout.write(self.style.SUCCESS('   ✓ All active rooms have faculty assignments'))

        # 6. Check Schedules
        self.stdout.write(self.style.WARNING('\n\n📅 CLASS SCHEDULES:\n'))
        schedules = ClassSchedule.objects.filter(is_active=True).select_related('course', 'course__faculty')
        schedules_without_faculty = [s for s in schedules if not s.course.faculty]
        
        if schedules_without_faculty:
            self.stdout.write(self.style.ERROR(f'   ⚠️  {len(schedules_without_faculty)} schedules with courses WITHOUT faculty'))
        else:
            self.stdout.write(self.style.SUCCESS('   ✓ All schedules have courses with faculty'))

        # 7. Faculty Statistics
        self.stdout.write(self.style.SUCCESS('\n\n📊 FACULTY STATISTICS:\n'))
        
        for faculty in Faculty.objects.filter(is_active=True):
            courses = Course.objects.filter(faculty=faculty, is_active=True).count()
            teachers = Teacher.objects.filter(faculty=faculty, is_active=True).count()
            floors = Floor.objects.filter(faculty=faculty, is_active=True).count()
            rooms = Room.objects.filter(faculty=faculty, is_active=True).count()
            schedules = ClassSchedule.objects.filter(
                course__faculty=faculty,
                is_active=True
            ).count()
            
            self.stdout.write(f'\n   🏛️  {faculty.faculty_name}:')
            self.stdout.write(f'      - Courses: {courses}')
            self.stdout.write(f'      - Teachers: {teachers}')
            self.stdout.write(f'      - Floors: {floors}')
            self.stdout.write(f'      - Rooms: {rooms}')
            self.stdout.write(f'      - Class Schedules: {schedules}')

        # 8. Check for data conflicts
        self.stdout.write(self.style.WARNING('\n\n⚠️  CHECKING FOR CONFLICTS:\n'))
        
        # Check if rooms are on floors of different faculties
        room_conflicts = []
        for room in Room.objects.filter(is_active=True).select_related('floor', 'faculty', 'floor__faculty'):
            if room.faculty and room.floor.faculty and room.faculty != room.floor.faculty:
                room_conflicts.append(room)
        
        if room_conflicts:
            self.stdout.write(self.style.ERROR(f'   ⚠️  {len(room_conflicts)} rooms on floors of DIFFERENT faculties:\n'))
            for room in room_conflicts[:5]:
                self.stdout.write(
                    f'      - Room {room.room_number}: Room faculty={room.faculty.faculty_name}, '
                    f'Floor faculty={room.floor.faculty.faculty_name}'
                )
            
            if options['fix']:
                for room in room_conflicts:
                    room.faculty = room.floor.faculty
                    room.save()
                self.stdout.write(self.style.SUCCESS(f'\n   ✓ Fixed {len(room_conflicts)} room conflicts'))
        else:
            self.stdout.write(self.style.SUCCESS('   ✓ No room-floor faculty conflicts'))

        # Summary
        self.stdout.write(self.style.SUCCESS('\n\n' + '='*70))
        self.stdout.write(self.style.SUCCESS('  AUDIT COMPLETE'))
        self.stdout.write(self.style.SUCCESS('='*70 + '\n'))
        
        if options['fix']:
            self.stdout.write(self.style.SUCCESS('✓ Fixes have been applied\n'))
        else:
            self.stdout.write(self.style.WARNING('ℹ️  Run with --fix to apply automatic fixes\n'))
            if faculties.count() > 0:
                first_faculty = faculties.first()
                self.stdout.write(
                    f'Example: python manage.py audit_faculty_data --fix --faculty {first_faculty.id}\n'
                )

