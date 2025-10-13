"""
Management command to populate database with sample data.

Usage:
    python manage.py populate_sample_data

This command creates:
- 6 floors
- Multiple rooms on each floor
- Sample teachers
- Sample courses
- Sample class schedules
"""

from django.core.management.base import BaseCommand
from classes.models import Teacher, Course, Floor, Room, ClassSchedule


class Command(BaseCommand):
    help = 'Populate database with sample data for testing'

    def handle(self, *args, **kwargs):
        """Execute the command"""
        
        self.stdout.write(self.style.WARNING('شروع افزودن داده‌های نمونه...'))
        
        # Create Floors
        self.stdout.write('ایجاد طبقات...')
        floors = []
        floor_names = ['طبقه اول', 'طبقه دوم', 'طبقه سوم', 'طبقه چهارم', 'طبقه پنجم', 'طبقه ششم']
        
        for i, name in enumerate(floor_names, 1):
            floor, created = Floor.objects.get_or_create(
                floor_number=i,
                defaults={'floor_name': name, 'is_active': True}
            )
            floors.append(floor)
            if created:
                self.stdout.write(self.style.SUCCESS(f'✓ {name} ایجاد شد'))
        
        # Create Rooms
        self.stdout.write('\nایجاد اتاق‌ها...')
        room_count = 0
        
        for floor in floors:
            # Create left rooms
            for i in range(1, 4):
                room_number = f"{floor.floor_number}0{i}"
                room, created = Room.objects.get_or_create(
                    floor=floor,
                    room_number=room_number,
                    defaults={
                        'room_type': 'classroom',
                        'capacity': 30 + (i * 5),
                        'position': 'left',
                        'is_active': True
                    }
                )
                if created:
                    room_count += 1
            
            # Create right rooms
            for i in range(4, 7):
                room_number = f"{floor.floor_number}0{i}"
                room, created = Room.objects.get_or_create(
                    floor=floor,
                    room_number=room_number,
                    defaults={
                        'room_type': 'classroom',
                        'capacity': 30 + (i * 5),
                        'position': 'right',
                        'is_active': True
                    }
                )
                if created:
                    room_count += 1
            
            # Create one center room (lab or study hall)
            room_number = f"{floor.floor_number}99"
            room, created = Room.objects.get_or_create(
                floor=floor,
                room_number=room_number,
                defaults={
                    'room_type': 'lab',
                    'capacity': 25,
                    'position': 'center',
                    'is_active': True
                }
            )
            if created:
                room_count += 1
        
        self.stdout.write(self.style.SUCCESS(f'✓ {room_count} اتاق ایجاد شد'))
        
        # Create Teachers
        self.stdout.write('\nایجاد اساتید...')
        teachers_data = [
            {'full_name': 'دکتر احمدی', 'email': 'ahmadi@university.ac.ir'},
            {'full_name': 'دکتر محمدی', 'email': 'mohammadi@university.ac.ir'},
            {'full_name': 'دکتر رضایی', 'email': 'rezaei@university.ac.ir'},
            {'full_name': 'دکتر حسینی', 'email': 'hosseini@university.ac.ir'},
            {'full_name': 'دکتر کریمی', 'email': 'karimi@university.ac.ir'},
            {'full_name': 'دکتر علوی', 'email': 'alavi@university.ac.ir'},
        ]
        
        teachers = []
        for data in teachers_data:
            teacher, created = Teacher.objects.get_or_create(
                full_name=data['full_name'],
                defaults={'email': data['email'], 'is_active': True}
            )
            teachers.append(teacher)
            if created:
                self.stdout.write(self.style.SUCCESS(f"✓ {data['full_name']} اضافه شد"))
        
        # Create Courses
        self.stdout.write('\nایجاد دروس...')
        courses_data = [
            {'course_code': 'AI-401', 'course_name': 'هوش مصنوعی پیشرفته', 'credit_hours': 3},
            {'course_code': 'ML-501', 'course_name': 'یادگیری ماشین', 'credit_hours': 3},
            {'course_code': 'ROB-301', 'course_name': 'مکاترونیک پیشرفته', 'credit_hours': 3},
            {'course_code': 'CV-402', 'course_name': 'بینایی کامپیوتر', 'credit_hours': 3},
            {'course_code': 'NLP-503', 'course_name': 'پردازش زبان طبیعی', 'credit_hours': 3},
            {'course_code': 'DS-201', 'course_name': 'علوم داده', 'credit_hours': 3},
            {'course_code': 'DL-601', 'course_name': 'یادگیری عمیق', 'credit_hours': 3},
            {'course_code': 'IOT-301', 'course_name': 'اینترنت اشیا', 'credit_hours': 2},
        ]
        
        courses = []
        for data in courses_data:
            course, created = Course.objects.get_or_create(
                course_code=data['course_code'],
                defaults={
                    'course_name': data['course_name'],
                    'credit_hours': data['credit_hours'],
                    'is_active': True
                }
            )
            courses.append(course)
            if created:
                self.stdout.write(self.style.SUCCESS(f"✓ {data['course_name']} اضافه شد"))
        
        # Create Sample Schedules
        self.stdout.write('\nایجاد برنامه‌های کلاسی نمونه...')
        schedule_count = 0
        
        # Sample schedules for Saturday
        days = ['saturday', 'sunday', 'monday', 'tuesday', 'wednesday']
        times = ['08:00', '10:30', '13:30', '16:30']
        
        rooms = Room.objects.filter(room_type='classroom', is_active=True)[:20]
        
        for idx, room in enumerate(rooms):
            day = days[idx % len(days)]
            time = times[idx % len(times)]
            teacher = teachers[idx % len(teachers)]
            course = courses[idx % len(courses)]
            
            try:
                schedule, created = ClassSchedule.objects.get_or_create(
                    room=room,
                    day_of_week=day,
                    time_slot=time,
                    defaults={
                        'teacher': teacher,
                        'course': course,
                        'semester': 'پاییز',
                        'academic_year': '1403-1404',
                        'is_holding': True,  # Most classes are holding by default
                        'is_active': True
                    }
                )
                if created:
                    schedule_count += 1
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'هشدار: {str(e)}'))
        
        self.stdout.write(self.style.SUCCESS(f'✓ {schedule_count} برنامه کلاسی ایجاد شد'))
        
        # Summary
        self.stdout.write(self.style.SUCCESS('\n' + '='*50))
        self.stdout.write(self.style.SUCCESS('✅ داده‌های نمونه با موفقیت اضافه شدند!'))
        self.stdout.write(self.style.SUCCESS('='*50))
        self.stdout.write(f'\n📊 خلاصه:')
        self.stdout.write(f'   • تعداد طبقات: {Floor.objects.count()}')
        self.stdout.write(f'   • تعداد اتاق‌ها: {Room.objects.count()}')
        self.stdout.write(f'   • تعداد اساتید: {Teacher.objects.count()}')
        self.stdout.write(f'   • تعداد دروس: {Course.objects.count()}')
        self.stdout.write(f'   • تعداد برنامه‌ها: {ClassSchedule.objects.count()}')
        self.stdout.write(f'\n🌐 برای مشاهده وبسایت: http://127.0.0.1:8000/')
        self.stdout.write(f'⚙️  برای ورود به پنل ادمین: http://127.0.0.1:8000/admin/\n')

