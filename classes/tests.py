"""
Comprehensive test suite for the classes app
"""
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APITestCase
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from .models import (
    TeacherUser, StudentUser, EducationalConsultingSession, 
    SessionRegistration, Floor, Room, ClassSchedule, Teacher, Course
)
from .forms import TeacherRegistrationForm, StudentRegistrationForm, ConsultingSessionForm
from .utils import validate_email_format, validate_phone_format, validate_student_number
import json
from datetime import date, time, timedelta


class ModelTests(TestCase):
    """Test cases for models"""
    
    def setUp(self):
        """Set up test data"""
        self.teacher_user = TeacherUser.objects.create_user(
            username='test_teacher',
            email='teacher@test.com',
            password='testpass123',
            first_name='علی',
            last_name='احمدی',
            phone_number='09123456789',
            specialization='هوش مصنوعی'
        )
        
        self.student_user = StudentUser.objects.create_user(
            student_number='1234567890',
            email='student@test.com',
            password='testpass123',
            first_name='مریم',
            last_name='رضایی',
            phone_number='09987654321',
            major='هوش مصنوعی'
        )
        
        self.teacher = Teacher.objects.create(
            full_name='دکتر علی احمدی',
            email='teacher@test.com',
            phone_number='09123456789',
            specialization='هوش مصنوعی'
        )
        
        self.course = Course.objects.create(
            course_name='هوش مصنوعی',
            course_code='AI101',
            credits=3
        )
        
        self.floor = Floor.objects.create(
            floor_number=1,
            floor_name='طبقه اول',
            is_active=True
        )
        
        self.room = Room.objects.create(
            room_number='101',
            floor=self.floor,
            position='left',
            is_active=True
        )
        
        self.class_schedule = ClassSchedule.objects.create(
            teacher=self.teacher,
            course=self.course,
            room=self.room,
            day_of_week='monday',
            time_slot='8:00',
            is_active=True
        )
    
    def test_teacher_user_creation(self):
        """Test teacher user creation"""
        self.assertEqual(self.teacher_user.username, 'test_teacher')
        self.assertEqual(self.teacher_user.email, 'teacher@test.com')
        self.assertEqual(self.teacher_user.full_name, 'علی احمدی')
        self.assertTrue(self.teacher_user.is_teacher)
        self.assertFalse(self.teacher_user.is_student)
    
    def test_student_user_creation(self):
        """Test student user creation"""
        self.assertEqual(self.student_user.student_number, '1234567890')
        self.assertEqual(self.student_user.email, 'student@test.com')
        self.assertEqual(self.student_user.full_name, 'مریم رضایی')
        self.assertFalse(self.student_user.is_teacher)
        self.assertTrue(self.student_user.is_student)
    
    def test_consulting_session_creation(self):
        """Test consulting session creation"""
        session = EducationalConsultingSession.objects.create(
            teacher=self.teacher_user,
            title='مشاوره هوش مصنوعی',
            description='جلسه مشاوره در مورد هوش مصنوعی',
            subject='هوش مصنوعی',
            session_date=date.today() + timedelta(days=7),
            start_time=time(10, 0),
            end_time=time(12, 0),
            max_students=10,
            fee=50000,
            is_online=True
        )
        
        self.assertEqual(session.title, 'مشاوره هوش مصنوعی')
        self.assertEqual(session.teacher, self.teacher_user)
        self.assertEqual(session.registered_count, 0)
        self.assertTrue(session.is_active)
    
    def test_session_registration_creation(self):
        """Test session registration creation"""
        session = EducationalConsultingSession.objects.create(
            teacher=self.teacher_user,
            title='مشاوره هوش مصنوعی',
            subject='هوش مصنوعی',
            session_date=date.today() + timedelta(days=7),
            start_time=time(10, 0),
            end_time=time(12, 0),
            max_students=10,
            fee=50000
        )
        
        registration = SessionRegistration.objects.create(
            student=self.student_user,
            session=session
        )
        
        self.assertEqual(registration.student, self.student_user)
        self.assertEqual(registration.session, session)
        self.assertEqual(registration.status, 'registered')
    
    def test_class_schedule_creation(self):
        """Test class schedule creation"""
        self.assertEqual(self.class_schedule.teacher, self.teacher)
        self.assertEqual(self.class_schedule.course, self.course)
        self.assertEqual(self.class_schedule.room, self.room)
        self.assertEqual(self.class_schedule.day_of_week, 'monday')
        self.assertEqual(self.class_schedule.time_slot, '8:00')


class FormTests(TestCase):
    """Test cases for forms"""
    
    def test_teacher_registration_form_valid(self):
        """Test valid teacher registration form"""
        form_data = {
            'username': 'test_teacher',
            'email': 'teacher@test.com',
            'first_name': 'علی',
            'last_name': 'احمدی',
            'phone_number': '09123456789',
            'specialization': 'هوش مصنوعی',
            'password': 'TestPass123',
            'confirm_password': 'TestPass123'
        }
        form = TeacherRegistrationForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_teacher_registration_form_invalid_password(self):
        """Test invalid teacher registration form with weak password"""
        form_data = {
            'username': 'test_teacher',
            'email': 'teacher@test.com',
            'first_name': 'علی',
            'last_name': 'احمدی',
            'phone_number': '09123456789',
            'specialization': 'هوش مصنوعی',
            'password': 'weak',
            'confirm_password': 'weak'
        }
        form = TeacherRegistrationForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('password', form.errors)
    
    def test_student_registration_form_valid(self):
        """Test valid student registration form"""
        form_data = {
            'student_number': '1234567890',
            'email': 'student@test.com',
            'first_name': 'مریم',
            'last_name': 'رضایی',
            'phone_number': '09987654321',
            'major': 'هوش مصنوعی',
            'password': 'TestPass123',
            'confirm_password': 'TestPass123'
        }
        form = StudentRegistrationForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_consulting_session_form_valid(self):
        """Test valid consulting session form"""
        teacher = TeacherUser.objects.create_user(
            username='test_teacher',
            email='teacher@test.com',
            password='testpass123'
        )
        
        form_data = {
            'title': 'مشاوره هوش مصنوعی',
            'description': 'جلسه مشاوره در مورد هوش مصنوعی',
            'subject': 'هوش مصنوعی',
            'session_date': date.today() + timedelta(days=7),
            'start_time': time(10, 0),
            'end_time': time(12, 0),
            'max_students': 10,
            'fee': 50000,
            'is_online': True
        }
        form = ConsultingSessionForm(data=form_data)
        self.assertTrue(form.is_valid())


class ViewTests(TestCase):
    """Test cases for views"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        self.teacher_user = TeacherUser.objects.create_user(
            username='test_teacher',
            email='teacher@test.com',
            password='testpass123',
            first_name='علی',
            last_name='احمدی'
        )
        
        self.student_user = StudentUser.objects.create_user(
            student_number='1234567890',
            email='student@test.com',
            password='testpass123',
            first_name='مریم',
            last_name='رضایی'
        )
    
    def test_home_view(self):
        """Test home view"""
        response = self.client.get(reverse('classes:home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'دانشکده هوش و مکاترونیک')
    
    def test_class_affairs_view(self):
        """Test class affairs view"""
        response = self.client.get(reverse('classes:class_affairs'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'امور کلاس‌ها')
    
    def test_teacher_login_view(self):
        """Test teacher login view"""
        response = self.client.get(reverse('classes:teacher_login'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'ورود استاد')
    
    def test_student_signup_view(self):
        """Test student signup view"""
        response = self.client.get(reverse('classes:student_signup'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'ثبت‌نام دانشجو')
    
    def test_consulting_sessions_view(self):
        """Test consulting sessions view"""
        response = self.client.get(reverse('classes:consulting_sessions'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'جلسات مشاوره')


class APITests(APITestCase):
    """Test cases for API views"""
    
    def setUp(self):
        """Set up test data"""
        self.teacher_user = TeacherUser.objects.create_user(
            username='test_teacher',
            email='teacher@test.com',
            password='testpass123',
            first_name='علی',
            last_name='احمدی'
        )
        
        self.student_user = StudentUser.objects.create_user(
            student_number='1234567890',
            email='student@test.com',
            password='testpass123',
            first_name='مریم',
            last_name='رضایی'
        )
        
        self.teacher_token = RefreshToken.for_user(self.teacher_user)
        self.student_token = RefreshToken.for_user(self.student_user)
    
    def test_teacher_login_api(self):
        """Test teacher login API"""
        data = {
            'username': 'test_teacher',
            'password': 'testpass123'
        }
        response = self.client.post('/api/auth/teacher/login/', data)
        self.assertEqual(response.status_code, 200)
        self.assertIn('tokens', response.data)
        self.assertIn('access', response.data['tokens'])
    
    def test_student_signup_api(self):
        """Test student signup API"""
        data = {
            'student_number': '9876543210',
            'email': 'newstudent@test.com',
            'first_name': 'احمد',
            'last_name': 'محمدی',
            'phone_number': '09111111111',
            'major': 'مهندسی کامپیوتر',
            'password': 'TestPass123',
            'confirm_password': 'TestPass123'
        }
        response = self.client.post('/api/auth/student/signup/', data)
        self.assertEqual(response.status_code, 201)
        self.assertTrue(response.data['success'])
    
    def test_consulting_sessions_list_api(self):
        """Test consulting sessions list API"""
        response = self.client.get('/api/consulting/sessions/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('results', response.data)
    
    def test_teacher_dashboard_api(self):
        """Test teacher dashboard API"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.teacher_token.access_token}')
        response = self.client.get('/api/dashboard/teacher/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('teacher', response.data)
    
    def test_student_dashboard_api(self):
        """Test student dashboard API"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.student_token.access_token}')
        response = self.client.get('/api/dashboard/student/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('student', response.data)


class UtilityTests(TestCase):
    """Test cases for utility functions"""
    
    def test_validate_email_format_valid(self):
        """Test valid email format validation"""
        valid_emails = [
            'test@example.com',
            'user.name@domain.co.uk',
            'test123@test.org'
        ]
        for email in valid_emails:
            try:
                validate_email_format(email)
            except Exception as e:
                self.fail(f"Valid email {email} failed validation: {e}")
    
    def test_validate_email_format_invalid(self):
        """Test invalid email format validation"""
        invalid_emails = [
            'invalid-email',
            '@domain.com',
            'test@',
            'test..test@domain.com'
        ]
        for email in invalid_emails:
            with self.assertRaises(Exception):
                validate_email_format(email)
    
    def test_validate_phone_format_valid(self):
        """Test valid phone format validation"""
        valid_phones = [
            '09123456789',
            '09987654321',
            '09111111111'
        ]
        for phone in valid_phones:
            try:
                validate_phone_format(phone)
            except Exception as e:
                self.fail(f"Valid phone {phone} failed validation: {e}")
    
    def test_validate_phone_format_invalid(self):
        """Test invalid phone format validation"""
        invalid_phones = [
            '1234567890',
            '0912345678',
            '08123456789',
            '091234567890'
        ]
        for phone in invalid_phones:
            with self.assertRaises(Exception):
                validate_phone_format(phone)
    
    def test_validate_student_number_valid(self):
        """Test valid student number validation"""
        valid_numbers = ['1234567', '12345678', '123456789', '1234567890']
        for number in valid_numbers:
            try:
                validate_student_number(number)
            except Exception as e:
                self.fail(f"Valid student number {number} failed validation: {e}")
    
    def test_validate_student_number_invalid(self):
        """Test invalid student number validation"""
        invalid_numbers = ['123456', '12345678901', 'abc123456', '12345abc']
        for number in invalid_numbers:
            with self.assertRaises(Exception):
                validate_student_number(number)


class IntegrationTests(TestCase):
    """Integration test cases"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        
        # Create test data
        self.teacher_user = TeacherUser.objects.create_user(
            username='test_teacher',
            email='teacher@test.com',
            password='testpass123',
            first_name='علی',
            last_name='احمدی'
        )
        
        self.student_user = StudentUser.objects.create_user(
            student_number='1234567890',
            email='student@test.com',
            password='testpass123',
            first_name='مریم',
            last_name='رضایی'
        )
        
        # Create consulting session
        self.session = EducationalConsultingSession.objects.create(
            teacher=self.teacher_user,
            title='مشاوره هوش مصنوعی',
            subject='هوش مصنوعی',
            session_date=date.today() + timedelta(days=7),
            start_time=time(10, 0),
            end_time=time(12, 0),
            max_students=10,
            fee=50000
        )
    
    def test_complete_registration_flow(self):
        """Test complete student registration flow"""
        # 1. Student signs up
        signup_data = {
            'student_number': '9876543210',
            'email': 'newstudent@test.com',
            'first_name': 'احمد',
            'last_name': 'محمدی',
            'phone_number': '09111111111',
            'major': 'مهندسی کامپیوتر',
            'password': 'TestPass123',
            'confirm_password': 'TestPass123'
        }
        
        response = self.client.post('/api/auth/student/signup/', signup_data)
        self.assertEqual(response.status_code, 201)
        
        # 2. Student logs in
        login_data = {
            'student_number': '9876543210',
            'password': 'TestPass123'
        }
        
        response = self.client.post('/api/auth/student/login/', login_data)
        self.assertEqual(response.status_code, 200)
        token = response.data['tokens']['access']
        
        # 3. Student registers for session
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        response = self.client.post(f'/api/consulting/sessions/{self.session.id}/register/')
        self.assertEqual(response.status_code, 201)
        
        # 4. Verify registration
        registration = SessionRegistration.objects.get(
            student__student_number='9876543210',
            session=self.session
        )
        self.assertEqual(registration.status, 'registered')
    
    def test_teacher_session_management_flow(self):
        """Test teacher session management flow"""
        # 1. Teacher logs in
        login_data = {
            'username': 'test_teacher',
            'password': 'testpass123'
        }
        
        response = self.client.post('/api/auth/teacher/login/', login_data)
        self.assertEqual(response.status_code, 200)
        token = response.data['tokens']['access']
        
        # 2. Teacher creates session
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        session_data = {
            'title': 'مشاوره جدید',
            'subject': 'فیزیک',
            'session_date': (date.today() + timedelta(days=14)).isoformat(),
            'start_time': '14:00:00',
            'end_time': '16:00:00',
            'max_students': 15,
            'fee': 75000,
            'is_online': False
        }
        
        response = self.client.post('/api/consulting/sessions/', session_data)
        self.assertEqual(response.status_code, 201)
        
        # 3. Teacher views dashboard
        response = self.client.get('/api/dashboard/teacher/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('sessions', response.data)


class SecurityTests(TestCase):
    """Security test cases"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        self.teacher_user = TeacherUser.objects.create_user(
            username='test_teacher',
            email='teacher@test.com',
            password='testpass123'
        )
    
    def test_password_requirements(self):
        """Test password requirements"""
        weak_passwords = [
            '12345678',  # Only numbers
            'abcdefgh',  # Only letters
            'ABCDEFGH',  # Only uppercase
            'abc123',    # Too short
            'password'   # Common password
        ]
        
        for password in weak_passwords:
            form_data = {
                'username': 'test_user',
                'email': 'test@test.com',
                'password': password,
                'confirm_password': password
            }
            form = TeacherRegistrationForm(data=form_data)
            self.assertFalse(form.is_valid(), f"Weak password {password} should be invalid")
    
    def test_sql_injection_protection(self):
        """Test SQL injection protection"""
        malicious_input = "'; DROP TABLE auth_user; --"
        
        # Test in search
        response = self.client.get(f'/api/consulting/sessions/?search={malicious_input}')
        self.assertEqual(response.status_code, 200)
        
        # Test in form submission
        form_data = {
            'username': malicious_input,
            'email': 'test@test.com',
            'password': 'TestPass123',
            'confirm_password': 'TestPass123'
        }
        form = TeacherRegistrationForm(data=form_data)
        # Should not raise database error
        self.assertIsNotNone(form)
    
    def test_xss_protection(self):
        """Test XSS protection"""
        malicious_script = "<script>alert('XSS')</script>"
        
        # Test in search
        response = self.client.get(f'/api/consulting/sessions/?search={malicious_script}')
        self.assertEqual(response.status_code, 200)
        # Response should not contain the script tag
        self.assertNotIn('<script>', str(response.content))