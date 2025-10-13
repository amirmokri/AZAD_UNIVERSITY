"""
Management command to check if the project is ready for deployment.

This command performs various checks to ensure the application is
properly configured for production deployment.
"""

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.core.checks import run_checks
import sys


class Command(BaseCommand):
    help = 'Check if the project is ready for deployment'

    def add_arguments(self, parser):
        parser.add_argument(
            '--strict',
            action='store_true',
            help='Fail on warnings',
        )

    def handle(self, *args, **options):
        strict = options['strict']
        issues_found = False
        
        self.stdout.write(self.style.SUCCESS('=' * 70))
        self.stdout.write(self.style.SUCCESS('Deployment Readiness Check'))
        self.stdout.write(self.style.SUCCESS('=' * 70))
        self.stdout.write('')

        # Check 1: SECRET_KEY
        self.stdout.write(self.style.WARNING('Checking SECRET_KEY...'))
        if settings.SECRET_KEY == 'django-insecure-change-this-in-production-abc123xyz':
            self.stdout.write(self.style.ERROR('  ❌ SECRET_KEY is using default value!'))
            self.stdout.write(self.style.WARNING('     Generate a new one: python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"'))
            issues_found = True
        else:
            self.stdout.write(self.style.SUCCESS('  ✅ SECRET_KEY is configured'))
        self.stdout.write('')

        # Check 2: DEBUG
        self.stdout.write(self.style.WARNING('Checking DEBUG setting...'))
        if settings.DEBUG:
            self.stdout.write(self.style.ERROR('  ❌ DEBUG is True! This should be False in production.'))
            issues_found = True
        else:
            self.stdout.write(self.style.SUCCESS('  ✅ DEBUG is False'))
        self.stdout.write('')

        # Check 3: ALLOWED_HOSTS
        self.stdout.write(self.style.WARNING('Checking ALLOWED_HOSTS...'))
        if not settings.ALLOWED_HOSTS or settings.ALLOWED_HOSTS == ['*']:
            self.stdout.write(self.style.ERROR('  ❌ ALLOWED_HOSTS is not properly configured!'))
            self.stdout.write(self.style.WARNING('     Set specific domains in production'))
            issues_found = True
        else:
            self.stdout.write(self.style.SUCCESS(f'  ✅ ALLOWED_HOSTS: {settings.ALLOWED_HOSTS}'))
        self.stdout.write('')

        # Check 4: Database
        self.stdout.write(self.style.WARNING('Checking database configuration...'))
        db_config = settings.DATABASES['default']
        if db_config['HOST'] == 'localhost' and not settings.DEBUG:
            self.stdout.write(self.style.ERROR('  ⚠️  Database host is localhost in production mode'))
            if strict:
                issues_found = True
        self.stdout.write(self.style.SUCCESS(f'  ✅ Database: {db_config["ENGINE"]}'))
        self.stdout.write(self.style.SUCCESS(f'     Host: {db_config["HOST"]}:{db_config["PORT"]}'))
        self.stdout.write('')

        # Check 5: Static/Media files
        self.stdout.write(self.style.WARNING('Checking static and media files configuration...'))
        use_s3 = getattr(settings, 'USE_S3_STORAGE', False)
        if use_s3:
            self.stdout.write(self.style.SUCCESS('  ✅ Using Arvan Cloud Object Storage'))
            if hasattr(settings, 'AWS_STORAGE_BUCKET_NAME'):
                self.stdout.write(self.style.SUCCESS(f'     Bucket: {settings.AWS_STORAGE_BUCKET_NAME}'))
            if hasattr(settings, 'AWS_S3_ENDPOINT_URL'):
                self.stdout.write(self.style.SUCCESS(f'     Endpoint: {settings.AWS_S3_ENDPOINT_URL}'))
        else:
            self.stdout.write(self.style.WARNING('  ⚠️  Using local file storage'))
            if not settings.DEBUG:
                self.stdout.write(self.style.ERROR('     Consider using Arvan Cloud in production'))
                if strict:
                    issues_found = True
        self.stdout.write('')

        # Check 6: Security settings
        self.stdout.write(self.style.WARNING('Checking security settings...'))
        security_checks = {
            'SECURE_SSL_REDIRECT': getattr(settings, 'SECURE_SSL_REDIRECT', False),
            'SESSION_COOKIE_SECURE': getattr(settings, 'SESSION_COOKIE_SECURE', False),
            'CSRF_COOKIE_SECURE': getattr(settings, 'CSRF_COOKIE_SECURE', False),
            'SECURE_HSTS_SECONDS': getattr(settings, 'SECURE_HSTS_SECONDS', 0) > 0,
        }
        
        for check_name, check_value in security_checks.items():
            if not settings.DEBUG and not check_value:
                self.stdout.write(self.style.ERROR(f'  ❌ {check_name} should be enabled in production'))
                if strict:
                    issues_found = True
            else:
                status = '✅' if check_value else '⚠️'
                self.stdout.write(self.style.SUCCESS(f'  {status} {check_name}: {check_value}'))
        self.stdout.write('')

        # Check 7: CORS settings
        self.stdout.write(self.style.WARNING('Checking CORS configuration...'))
        if getattr(settings, 'CORS_ALLOW_ALL_ORIGINS', False) and not settings.DEBUG:
            self.stdout.write(self.style.ERROR('  ❌ CORS_ALLOW_ALL_ORIGINS is True in production!'))
            self.stdout.write(self.style.WARNING('     Specify exact origins for security'))
            issues_found = True
        else:
            self.stdout.write(self.style.SUCCESS('  ✅ CORS configuration looks good'))
        self.stdout.write('')

        # Check 8: Run Django system checks
        self.stdout.write(self.style.WARNING('Running Django system checks...'))
        checks = run_checks(tags=None, include_deployment_checks=not settings.DEBUG)
        if checks:
            for check in checks:
                level = check.level
                if level >= 30:  # ERROR or CRITICAL
                    self.stdout.write(self.style.ERROR(f'  ❌ {check.msg}'))
                    issues_found = True
                else:
                    self.stdout.write(self.style.WARNING(f'  ⚠️  {check.msg}'))
                    if strict:
                        issues_found = True
        else:
            self.stdout.write(self.style.SUCCESS('  ✅ All system checks passed'))
        self.stdout.write('')

        # Check 9: Required packages
        self.stdout.write(self.style.WARNING('Checking required packages...'))
        required_packages = [
            ('django', 'Django'),
            ('rest_framework', 'Django REST Framework'),
            ('storages', 'django-storages'),
            ('boto3', 'boto3'),
            ('gunicorn', 'gunicorn'),
            ('decouple', 'python-decouple'),
        ]
        
        for package_name, display_name in required_packages:
            try:
                __import__(package_name)
                self.stdout.write(self.style.SUCCESS(f'  ✅ {display_name} is installed'))
            except ImportError:
                self.stdout.write(self.style.ERROR(f'  ❌ {display_name} is not installed!'))
                issues_found = True
        self.stdout.write('')

        # Final summary
        self.stdout.write(self.style.SUCCESS('=' * 70))
        if issues_found:
            if strict:
                self.stdout.write(self.style.ERROR('❌ DEPLOYMENT CHECK FAILED'))
                self.stdout.write(self.style.WARNING('Please fix the issues above before deploying.'))
                sys.exit(1)
            else:
                self.stdout.write(self.style.WARNING('⚠️  DEPLOYMENT CHECK COMPLETED WITH WARNINGS'))
                self.stdout.write(self.style.WARNING('Review the issues above before deploying.'))
        else:
            self.stdout.write(self.style.SUCCESS('✅ DEPLOYMENT CHECK PASSED'))
            self.stdout.write(self.style.SUCCESS('Your application is ready for deployment!'))
        self.stdout.write(self.style.SUCCESS('=' * 70))

