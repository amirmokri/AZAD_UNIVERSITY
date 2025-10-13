"""
Django settings for university_hub project.

This configuration file includes:
- MySQL database setup
- Django REST Framework configuration
- Static and media files configuration
- Security settings
- Installed apps configuration

For production deployment, ensure to:
- Change SECRET_KEY
- Set DEBUG = False
- Configure ALLOWED_HOSTS properly
- Use environment variables for sensitive data
"""

from pathlib import Path
import os
from decouple import config, Csv

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config('SECRET_KEY', default='django-insecure-change-this-in-production-abc123xyz')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config('DEBUG', default=True, cast=bool)

# Allow all hosts in development, restrict in production
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='*', cast=Csv())


# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Third-party apps
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
    'django_filters',
    'django_extensions',
    'django_elasticsearch_dsl',
    'storages',  # Django storages for cloud storage
    
    # Local apps
    'classes',  # Main app for class management
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',  # CORS middleware for API (must be before CommonMiddleware)
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'university_hub.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],  # Project-level templates
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.media',  # For media files
            ],
        },
    },
]

WSGI_APPLICATION = 'university_hub.wsgi.application'


# Database Configuration
# MySQL database setup for scalable and robust data storage
# NOTE: Create database first: CREATE DATABASE university_hub CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': config('DB_NAME', default='university_hub'),
        'USER': config('DB_USER', default='root'),
        'PASSWORD': config('DB_PASSWORD', default='232330scmj'),
        'HOST': config('DB_HOST', default='localhost'),
        'PORT': config('DB_PORT', default='3306'),
        'OPTIONS': {
            'charset': 'utf8mb4',
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
            'connect_timeout': 10,
        },
        'CONN_MAX_AGE': config('DB_CONN_MAX_AGE', default=600, cast=int),  # Connection pooling
    }
}


# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 8,
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# Configured for Persian/Farsi language support
LANGUAGE_CODE = 'fa-ir'  # Persian language

TIME_ZONE = 'Asia/Tehran'  # Tehran timezone

USE_I18N = True

USE_TZ = True

# Custom User Models
# AUTH_USER_MODEL = 'classes.TeacherUser'  # Primary user model for admin
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
]

# CSRF Settings
CSRF_COOKIE_SAMESITE = config('CSRF_COOKIE_SAMESITE', default='Lax')
CSRF_COOKIE_HTTPONLY = config('CSRF_COOKIE_HTTPONLY', default=True, cast=bool)
CSRF_COOKIE_SECURE = config('CSRF_COOKIE_SECURE', default=False, cast=bool)
CSRF_COOKIE_AGE = config('CSRF_COOKIE_AGE', default=3600, cast=int)
CSRF_TRUSTED_ORIGINS = config(
    'CSRF_TRUSTED_ORIGINS',
    default='http://localhost:8000,http://127.0.0.1:8000,http://localhost:3000,http://127.0.0.1:3000',
    cast=Csv()
)

# JWT Configuration
from datetime import timedelta

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=24),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'VERIFYING_KEY': None,
    'AUDIENCE': None,
    'ISSUER': None,
    'JWK_URL': None,
    'LEEWAY': 0,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    'USER_AUTHENTICATION_RULE': 'rest_framework_simplejwt.authentication.default_user_authentication_rule',
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',
    'JTI_CLAIM': 'jti',
    'SLIDING_TOKEN_REFRESH_EXP_CLAIM': 'refresh_exp',
    'SLIDING_TOKEN_LIFETIME': timedelta(hours=24),
    'SLIDING_TOKEN_REFRESH_LIFETIME': timedelta(days=7),
}


# Static files (CSS, JavaScript, Images)
# Configuration for serving static assets
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'  # Collected static files for production
STATICFILES_DIRS = [
    BASE_DIR / 'static',  # Development static files
]

# Arvan Cloud Object Storage Configuration
# Use environment variables for production
USE_S3_STORAGE = config('USE_S3_STORAGE', default=False, cast=bool)

if USE_S3_STORAGE:
    # AWS S3 settings for Arvan Cloud (S3-compatible)
    AWS_ACCESS_KEY_ID = config('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = config('AWS_SECRET_ACCESS_KEY')
    AWS_STORAGE_BUCKET_NAME = config('AWS_STORAGE_BUCKET_NAME')
    AWS_S3_ENDPOINT_URL = config('AWS_S3_ENDPOINT_URL', default='https://s3.ir-thr-at1.arvanstorage.ir')
    AWS_S3_REGION_NAME = config('AWS_S3_REGION_NAME', default='ir-thr-at1')
    AWS_S3_CUSTOM_DOMAIN = f'{AWS_STORAGE_BUCKET_NAME}.s3.ir-thr-at1.arvanstorage.ir'
    
    # S3 settings
    AWS_S3_OBJECT_PARAMETERS = {
        'CacheControl': 'max-age=86400',
    }
    AWS_S3_FILE_OVERWRITE = False
    AWS_DEFAULT_ACL = 'public-read'
    AWS_QUERYSTRING_AUTH = False
    AWS_S3_VERIFY = True
    AWS_S3_USE_SSL = True
    
    # Static files storage - use custom backend for proper location handling
    STATICFILES_STORAGE = 'university_hub.storage_backends.StaticStorage'
    
    # Media files storage - use custom backend for proper location handling
    DEFAULT_FILE_STORAGE = 'university_hub.storage_backends.MediaStorage'
    
    # URLs for static and media files
    STATIC_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/static/'
    MEDIA_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/media/'
else:
    # Local file storage for development
    MEDIA_URL = '/media/'
    MEDIA_ROOT = BASE_DIR / 'media'


# Django REST Framework Configuration
# Settings for API endpoints and permissions
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.AllowAny',  # Allow public access to read data
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 50,  # Pagination for large datasets
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    ],
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.FormParser',
        'rest_framework.parsers.MultiPartParser',
    ],
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
}


# CORS Configuration
# Allow API access from frontend
CORS_ALLOW_ALL_ORIGINS = config('CORS_ALLOW_ALL_ORIGINS', default=True, cast=bool)
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOWED_ORIGINS = config(
    'CORS_ALLOWED_ORIGINS',
    default='http://localhost:3000,http://127.0.0.1:3000,http://localhost:8000,http://127.0.0.1:8000',
    cast=Csv()
)


# Admin Site Configuration
# Customize admin panel appearance
ADMIN_SITE_HEADER = "دانشکده هوش و مکاترونیک - پنل مدیریت"
ADMIN_SITE_TITLE = "مدیریت کلاس‌ها"
ADMIN_INDEX_TITLE = "خوش آمدید به پنل مدیریت"

# Security settings
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'
SECURE_CROSS_ORIGIN_OPENER_POLICY = 'same-origin'

# SSL/HTTPS Settings
SECURE_SSL_REDIRECT = config('SECURE_SSL_REDIRECT', default=False, cast=bool)
SECURE_HSTS_SECONDS = config('SECURE_HSTS_SECONDS', default=0, cast=int)
SECURE_HSTS_INCLUDE_SUBDOMAINS = config('SECURE_HSTS_INCLUDE_SUBDOMAINS', default=False, cast=bool)
SECURE_HSTS_PRELOAD = config('SECURE_HSTS_PRELOAD', default=False, cast=bool)
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Cookie Security
SESSION_COOKIE_SECURE = config('SESSION_COOKIE_SECURE', default=False, cast=bool)
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
SESSION_COOKIE_AGE = config('SESSION_COOKIE_AGE', default=3600, cast=int)
SESSION_EXPIRE_AT_BROWSER_CLOSE = config('SESSION_EXPIRE_AT_BROWSER_CLOSE', default=True, cast=bool)
SESSION_SAVE_EVERY_REQUEST = config('SESSION_SAVE_EVERY_REQUEST', default=False, cast=bool)

# Clickjacking Protection
X_FRAME_OPTIONS = 'DENY'

# File Upload Security
FILE_UPLOAD_MAX_MEMORY_SIZE = config('FILE_UPLOAD_MAX_MEMORY_SIZE', default=5242880, cast=int)  # 5MB
DATA_UPLOAD_MAX_MEMORY_SIZE = config('DATA_UPLOAD_MAX_MEMORY_SIZE', default=5242880, cast=int)  # 5MB
DATA_UPLOAD_MAX_NUMBER_FIELDS = config('DATA_UPLOAD_MAX_NUMBER_FIELDS', default=1000, cast=int)

# Elasticsearch Configuration
ELASTICSEARCH_DSL = {
    'default': {
        'hosts': config('ELASTICSEARCH_HOST', default='http://localhost:9200'),
        'timeout': 30,
    },
}

# Elasticsearch Auto Sync - Set to False to avoid errors when Elasticsearch is not running
ELASTICSEARCH_DSL_AUTOSYNC = config('ELASTICSEARCH_DSL_AUTOSYNC', default=False, cast=bool)
ELASTICSEARCH_DSL_AUTO_REFRESH = config('ELASTICSEARCH_DSL_AUTO_REFRESH', default=False, cast=bool)

# Logging Configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse',
        },
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue',
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'console_debug': {
            'level': 'DEBUG',
            'filters': ['require_debug_true'],
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': config('LOG_LEVEL', default='INFO'),
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': config('DJANGO_LOG_LEVEL', default='INFO'),
            'propagate': False,
        },
        'django.request': {
            'handlers': ['console'],
            'level': 'ERROR',
            'propagate': False,
        },
        'django.security': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
        },
        'classes': {
            'handlers': ['console', 'console_debug'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# Performance Settings
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Template Caching (enable in production)
if not DEBUG:
    TEMPLATES[0]['OPTIONS']['loaders'] = [
        ('django.template.loaders.cached.Loader', [
            'django.template.loaders.filesystem.Loader',
            'django.template.loaders.app_directories.Loader',
        ]),
    ]

