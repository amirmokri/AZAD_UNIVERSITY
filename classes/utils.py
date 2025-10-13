"""
Utility functions for error handling and common operations
"""
import logging
from django.http import JsonResponse
from django.core.exceptions import ValidationError
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler
import traceback

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    """
    Custom exception handler for DRF API views
    """
    response = exception_handler(exc, context)
    
    if response is not None:
        custom_response_data = {
            'success': False,
            'error': 'خطا در پردازش درخواست',
            'details': response.data if isinstance(response.data, dict) else str(response.data),
            'status_code': response.status_code
        }
        
        # Log the error
        logger.error(f"API Error: {exc.__class__.__name__}: {str(exc)}")
        logger.error(f"Context: {context}")
        
        response.data = custom_response_data
    
    return response


def handle_api_error(error_message, status_code=status.HTTP_400_BAD_REQUEST, details=None):
    """
    Handle API errors with consistent response format
    """
    return Response({
        'success': False,
        'error': error_message,
        'details': details,
        'status_code': status_code
    }, status=status_code)


def handle_validation_error(validation_error):
    """
    Handle Django validation errors
    """
    if hasattr(validation_error, 'message_dict'):
        error_details = validation_error.message_dict
    else:
        error_details = str(validation_error)
    
    return handle_api_error(
        error_message='خطا در اعتبارسنجی داده‌ها',
        status_code=status.HTTP_400_BAD_REQUEST,
        details=error_details
    )


def handle_database_error(database_error):
    """
    Handle database-related errors
    """
    logger.error(f"Database Error: {str(database_error)}")
    logger.error(traceback.format_exc())
    
    return handle_api_error(
        error_message='خطا در پایگاه داده',
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        details='خطا در ذخیره یا بازیابی اطلاعات'
    )


def handle_authentication_error():
    """
    Handle authentication errors
    """
    return handle_api_error(
        error_message='احراز هویت ناموفق',
        status_code=status.HTTP_401_UNAUTHORIZED,
        details='لطفاً ابتدا وارد شوید'
    )


def handle_permission_error():
    """
    Handle permission errors
    """
    return handle_api_error(
        error_message='دسترسی غیرمجاز',
        status_code=status.HTTP_403_FORBIDDEN,
        details='شما دسترسی لازم برای انجام این عملیات را ندارید'
    )


def handle_not_found_error(resource_name='منبع'):
    """
    Handle not found errors
    """
    return handle_api_error(
        error_message=f'{resource_name} یافت نشد',
        status_code=status.HTTP_404_NOT_FOUND,
        details=f'لطفاً شناسه {resource_name} را بررسی کنید'
    )


def log_error(error, context=None):
    """
    Log errors with context information
    """
    error_info = {
        'error_type': error.__class__.__name__,
        'error_message': str(error),
        'traceback': traceback.format_exc(),
        'context': context
    }
    
    logger.error(f"Error occurred: {error_info}")


def safe_execute(func, *args, **kwargs):
    """
    Safely execute a function with error handling
    """
    try:
        return func(*args, **kwargs)
    except ValidationError as e:
        return handle_validation_error(e)
    except Exception as e:
        log_error(e, {'function': func.__name__, 'args': args, 'kwargs': kwargs})
        return handle_api_error(
            error_message='خطای غیرمنتظره',
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details='خطایی در سرور رخ داده است'
        )


def validate_required_fields(data, required_fields):
    """
    Validate that all required fields are present in data
    """
    missing_fields = []
    for field in required_fields:
        if field not in data or not data[field]:
            missing_fields.append(field)
    
    if missing_fields:
        raise ValidationError({
            'missing_fields': missing_fields,
            'message': f'فیلدهای اجباری: {", ".join(missing_fields)}'
        })


def validate_email_format(email):
    """
    Validate email format
    """
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(pattern, email):
        raise ValidationError('فرمت ایمیل نامعتبر است')


def validate_phone_format(phone):
    """
    Validate phone number format (Iranian format)
    """
    import re
    # Remove any non-digit characters
    phone_digits = re.sub(r'\D', '', phone)
    
    # Check if it's a valid Iranian phone number
    if not (phone_digits.startswith('09') and len(phone_digits) == 11):
        raise ValidationError('فرمت شماره تلفن نامعتبر است (مثال: 09123456789)')


def validate_student_number(student_number):
    """
    Validate student number format
    """
    import re
    # Student number should be numeric and reasonable length
    if not re.match(r'^\d{7,10}$', str(student_number)):
        raise ValidationError('شماره دانشجویی باید 7 تا 10 رقم باشد')


def format_error_message(error):
    """
    Format error message for user display
    """
    if isinstance(error, ValidationError):
        if hasattr(error, 'message_dict'):
            # Django form validation error
            messages = []
            for field, errors in error.message_dict.items():
                if isinstance(errors, list):
                    messages.extend([f"{field}: {msg}" for msg in errors])
                else:
                    messages.append(f"{field}: {errors}")
            return "؛ ".join(messages)
        else:
            return str(error)
    else:
        return str(error)


def create_success_response(data=None, message='عملیات با موفقیت انجام شد'):
    """
    Create a consistent success response
    """
    response_data = {
        'success': True,
        'message': message
    }
    
    if data is not None:
        response_data['data'] = data
    
    return response_data


def create_error_response(error_message, details=None, status_code=400):
    """
    Create a consistent error response
    """
    response_data = {
        'success': False,
        'error': error_message
    }
    
    if details:
        response_data['details'] = details
    
    return response_data, status_code


class APIResponseMixin:
    """
    Mixin for consistent API responses
    """
    
    def success_response(self, data=None, message='عملیات با موفقیت انجام شد'):
        return Response(create_success_response(data, message))
    
    def error_response(self, error_message, details=None, status_code=400):
        return Response(
            create_error_response(error_message, details, status_code)[0],
            status=create_error_response(error_message, details, status_code)[1]
        )
