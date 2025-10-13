"""
Security configurations and utilities
"""
from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.utils.deprecation import MiddlewareMixin
from django.utils import timezone
from django.core.cache import cache
import logging
import hashlib
import hmac
import time

logger = logging.getLogger(__name__)


class SecurityMiddleware(MiddlewareMixin):
    """
    Custom security middleware for additional protection
    """
    
    def process_request(self, request):
        """Process incoming requests for security checks"""
        # Rate limiting
        self._check_rate_limit(request)
        
        # IP whitelist/blacklist (if configured)
        self._check_ip_access(request)
        
        # Request size limit
        self._check_request_size(request)
        
        return None
    
    def _check_rate_limit(self, request):
        """Check rate limiting for API endpoints"""
        if request.path.startswith('/api/'):
            client_ip = self._get_client_ip(request)
            cache_key = f"rate_limit_{client_ip}_{request.path}"
            
            # Get current request count
            current_requests = cache.get(cache_key, 0)
            
            # Set rate limit (100 requests per minute)
            if current_requests >= 100:
                logger.warning(f"Rate limit exceeded for IP: {client_ip}")
                raise PermissionDenied("تعداد درخواست‌ها بیش از حد مجاز است")
            
            # Increment counter
            cache.set(cache_key, current_requests + 1, 60)  # 60 seconds
    
    def _check_ip_access(self, request):
        """Check IP access restrictions"""
        client_ip = self._get_client_ip(request)
        
        # Check blacklist
        blacklisted_ips = getattr(settings, 'SECURITY_BLACKLISTED_IPS', [])
        if client_ip in blacklisted_ips:
            logger.warning(f"Blacklisted IP attempted access: {client_ip}")
            raise PermissionDenied("دسترسی از این IP مجاز نیست")
        
        # Check whitelist (if configured)
        whitelisted_ips = getattr(settings, 'SECURITY_WHITELISTED_IPS', None)
        if whitelisted_ips and client_ip not in whitelisted_ips:
            logger.warning(f"Non-whitelisted IP attempted access: {client_ip}")
            raise PermissionDenied("دسترسی از این IP مجاز نیست")
    
    def _check_request_size(self, request):
        """Check request size limits"""
        content_length = request.META.get('CONTENT_LENGTH', 0)
        max_size = getattr(settings, 'SECURITY_MAX_REQUEST_SIZE', 10 * 1024 * 1024)  # 10MB
        
        if content_length and int(content_length) > max_size:
            logger.warning(f"Request size exceeded: {content_length} bytes")
            raise PermissionDenied("حجم درخواست بیش از حد مجاز است")
    
    def _get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class CSRFProtection:
    """
    Enhanced CSRF protection
    """
    
    @staticmethod
    def generate_csrf_token(user_id, session_key):
        """Generate CSRF token"""
        timestamp = str(int(time.time()))
        data = f"{user_id}:{session_key}:{timestamp}"
        token = hmac.new(
            settings.SECRET_KEY.encode(),
            data.encode(),
            hashlib.sha256
        ).hexdigest()
        return f"{token}:{timestamp}"
    
    @staticmethod
    def verify_csrf_token(token, user_id, session_key, max_age=3600):
        """Verify CSRF token"""
        try:
            token_part, timestamp = token.split(':')
            token_age = int(time.time()) - int(timestamp)
            
            if token_age > max_age:
                return False
            
            expected_data = f"{user_id}:{session_key}:{timestamp}"
            expected_token = hmac.new(
                settings.SECRET_KEY.encode(),
                expected_data.encode(),
                hashlib.sha256
            ).hexdigest()
            
            return hmac.compare_digest(token_part, expected_token)
        except (ValueError, TypeError):
            return False


class InputSanitizer:
    """
    Input sanitization utilities
    """
    
    @staticmethod
    def sanitize_string(value):
        """Sanitize string input"""
        if not isinstance(value, str):
            return value
        
        # Remove null bytes
        value = value.replace('\x00', '')
        
        # Remove control characters except newlines and tabs
        import re
        value = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', value)
        
        # Limit length
        max_length = getattr(settings, 'SECURITY_MAX_INPUT_LENGTH', 10000)
        if len(value) > max_length:
            value = value[:max_length]
        
        return value.strip()
    
    @staticmethod
    def sanitize_html(value):
        """Sanitize HTML input"""
        if not isinstance(value, str):
            return value
        
        # Remove script tags
        import re
        value = re.sub(r'<script[^>]*>.*?</script>', '', value, flags=re.IGNORECASE | re.DOTALL)
        
        # Remove javascript: protocols
        value = re.sub(r'javascript:', '', value, flags=re.IGNORECASE)
        
        # Remove on* attributes
        value = re.sub(r'\s+on\w+\s*=\s*["\'][^"\']*["\']', '', value, flags=re.IGNORECASE)
        
        return value
    
    @staticmethod
    def validate_file_upload(file):
        """Validate file upload"""
        # Check file size
        max_size = getattr(settings, 'SECURITY_MAX_FILE_SIZE', 5 * 1024 * 1024)  # 5MB
        if file.size > max_size:
            raise ValueError("حجم فایل بیش از حد مجاز است")
        
        # Check file type
        allowed_extensions = getattr(settings, 'SECURITY_ALLOWED_FILE_EXTENSIONS', ['.jpg', '.jpeg', '.png', '.pdf'])
        import os
        file_extension = os.path.splitext(file.name)[1].lower()
        if file_extension not in allowed_extensions:
            raise ValueError("نوع فایل مجاز نیست")
        
        return True


class PasswordSecurity:
    """
    Password security utilities
    """
    
    @staticmethod
    def check_password_strength(password):
        """Check password strength"""
        if len(password) < 8:
            return False, "رمز عبور باید حداقل 8 کاراکتر باشد"
        
        if not any(c.isupper() for c in password):
            return False, "رمز عبور باید حداقل یک حرف بزرگ داشته باشد"
        
        if not any(c.islower() for c in password):
            return False, "رمز عبور باید حداقل یک حرف کوچک داشته باشد"
        
        if not any(c.isdigit() for c in password):
            return False, "رمز عبور باید حداقل یک عدد داشته باشد"
        
        # Check for common passwords
        common_passwords = [
            'password', '123456', '123456789', 'qwerty', 'abc123',
            'password123', 'admin', 'letmein', 'welcome', 'monkey'
        ]
        if password.lower() in common_passwords:
            return False, "رمز عبور انتخاب شده رایج است"
        
        return True, "رمز عبور قوی است"
    
    @staticmethod
    def hash_password(password, salt=None):
        """Hash password with salt"""
        import secrets
        if salt is None:
            salt = secrets.token_hex(32)
        
        password_hash = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt.encode('utf-8'),
            100000  # iterations
        )
        
        return f"{salt}:{password_hash.hex()}"
    
    @staticmethod
    def verify_password(password, password_hash):
        """Verify password against hash"""
        try:
            salt, hash_part = password_hash.split(':')
            expected_hash = hashlib.pbkdf2_hmac(
                'sha256',
                password.encode('utf-8'),
                salt.encode('utf-8'),
                100000
            )
            return hmac.compare_digest(hash_part, expected_hash.hex())
        except (ValueError, TypeError):
            return False


class SessionSecurity:
    """
    Session security utilities
    """
    
    @staticmethod
    def create_secure_session(request, user):
        """Create secure session"""
        # Set session timeout
        request.session.set_expiry(3600)  # 1 hour
        
        # Set secure flags
        request.session['_auth_user_id'] = str(user.id)
        request.session['_auth_user_backend'] = user.backend
        request.session['_session_security'] = True
        
        # Generate session token
        session_token = CSRFProtection.generate_csrf_token(
            user.id,
            request.session.session_key
        )
        request.session['_session_token'] = session_token
        
        return session_token
    
    @staticmethod
    def validate_session(request):
        """Validate session security"""
        if not request.session.get('_session_security'):
            return False
        
        user_id = request.session.get('_auth_user_id')
        session_key = request.session.session_key
        session_token = request.session.get('_session_token')
        
        if not all([user_id, session_key, session_token]):
            return False
        
        return CSRFProtection.verify_csrf_token(
            session_token,
            user_id,
            session_key
        )


class AuditLogger:
    """
    Security audit logging
    """
    
    @staticmethod
    def log_security_event(event_type, user, request, details=None):
        """Log security events"""
        log_data = {
            'event_type': event_type,
            'user_id': user.id if user else None,
            'user_type': getattr(user, 'user_type', None) if user else None,
            'ip_address': request.META.get('REMOTE_ADDR'),
            'user_agent': request.META.get('HTTP_USER_AGENT'),
            'timestamp': timezone.now().isoformat(),
            'details': details or {}
        }
        
        logger.warning(f"Security Event: {log_data}")
    
    @staticmethod
    def log_failed_login(username, ip_address, user_agent):
        """Log failed login attempts"""
        AuditLogger.log_security_event(
            'failed_login',
            None,
            type('Request', (), {'META': {'REMOTE_ADDR': ip_address, 'HTTP_USER_AGENT': user_agent}})(),
            {'username': username}
        )
    
    @staticmethod
    def log_successful_login(user, request):
        """Log successful login"""
        AuditLogger.log_security_event(
            'successful_login',
            user,
            request
        )
    
    @staticmethod
    def log_suspicious_activity(user, request, activity_type, details):
        """Log suspicious activity"""
        AuditLogger.log_security_event(
            'suspicious_activity',
            user,
            request,
            {'activity_type': activity_type, 'details': details}
        )


class DataEncryption:
    """
    Data encryption utilities
    """
    
    @staticmethod
    def encrypt_sensitive_data(data, key=None):
        """Encrypt sensitive data"""
        from cryptography.fernet import Fernet
        import base64
        
        if key is None:
            key = settings.SECRET_KEY[:32].encode()
        
        # Generate key from secret
        key = base64.urlsafe_b64encode(key)
        fernet = Fernet(key)
        
        encrypted_data = fernet.encrypt(data.encode())
        return base64.urlsafe_b64encode(encrypted_data).decode()
    
    @staticmethod
    def decrypt_sensitive_data(encrypted_data, key=None):
        """Decrypt sensitive data"""
        from cryptography.fernet import Fernet
        import base64
        
        if key is None:
            key = settings.SECRET_KEY[:32].encode()
        
        # Generate key from secret
        key = base64.urlsafe_b64encode(key)
        fernet = Fernet(key)
        
        encrypted_data = base64.urlsafe_b64decode(encrypted_data.encode())
        decrypted_data = fernet.decrypt(encrypted_data)
        return decrypted_data.decode()


def require_https(view_func):
    """
    Decorator to require HTTPS
    """
    def wrapper(request, *args, **kwargs):
        if not request.is_secure() and not settings.DEBUG:
            from django.http import HttpResponsePermanentRedirect
            return HttpResponsePermanentRedirect(
                request.build_absolute_uri().replace('http://', 'https://')
            )
        return view_func(request, *args, **kwargs)
    return wrapper


def require_ajax(view_func):
    """
    Decorator to require AJAX requests
    """
    def wrapper(request, *args, **kwargs):
        if not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            raise Http404("AJAX request required")
        return view_func(request, *args, **kwargs)
    return wrapper
