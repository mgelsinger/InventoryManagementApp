import time
import logging
from django.utils.deprecation import MiddlewareMixin
from .logging_utils import log_view_access, get_client_ip

logger = logging.getLogger('inventory')


class RequestLoggingMiddleware(MiddlewareMixin):
    """Middleware to log all requests and responses"""
    
    def process_request(self, request):
        """Log incoming request"""
        try:
            request.start_time = time.time()
            
            # Skip logging for static files and media
            if request.path.startswith(('/static/', '/media/', '/admin/jsi18n/')):
                return None
            
            user = getattr(request, 'user', None)
            user_info = f"{user.username} (ID: {user.id})" if user and user.is_authenticated else "Anonymous"
            ip_address = get_client_ip(request)
            
            logger.info(
                f"Request started - Method: {request.method}, Path: {request.path}, "
                f"User: {user_info}, IP: {ip_address}"
            )
            
        except Exception as e:
            logger.error(f"Error in request logging middleware: {str(e)}")
        
        return None
    
    def process_response(self, request, response):
        """Log response"""
        try:
            # Skip logging for static files and media
            if request.path.startswith(('/static/', '/media/', '/admin/jsi18n/')):
                return response
            
            if hasattr(request, 'start_time'):
                response_time = time.time() - request.start_time
            else:
                response_time = 0
            
            user = getattr(request, 'user', None)
            user_info = f"{user.username} (ID: {user.id})" if user and user.is_authenticated else "Anonymous"
            ip_address = get_client_ip(request)
            status_code = response.status_code
            
            # Log based on status code
            if status_code >= 400:
                logger.warning(
                    f"Request completed with error - Method: {request.method}, Path: {request.path}, "
                    f"Status: {status_code}, User: {user_info}, IP: {ip_address}, "
                    f"Response Time: {response_time:.3f}s"
                )
            else:
                logger.info(
                    f"Request completed successfully - Method: {request.method}, Path: {request.path}, "
                    f"Status: {status_code}, User: {user_info}, IP: {ip_address}, "
                    f"Response Time: {response_time:.3f}s"
                )
            
        except Exception as e:
            logger.error(f"Error in response logging middleware: {str(e)}")
        
        return response
    
    def process_exception(self, request, exception):
        """Log exceptions"""
        try:
            user = getattr(request, 'user', None)
            user_info = f"{user.username} (ID: {user.id})" if user and user.is_authenticated else "Anonymous"
            ip_address = get_client_ip(request)
            
            if hasattr(request, 'start_time'):
                response_time = time.time() - request.start_time
            else:
                response_time = 0
            
            logger.error(
                f"Request exception - Method: {request.method}, Path: {request.path}, "
                f"User: {user_info}, IP: {ip_address}, Exception: {str(exception)}, "
                f"Response Time: {response_time:.3f}s"
            )
            
        except Exception as e:
            logger.error(f"Error in exception logging middleware: {str(e)}")
        
        return None


class SecurityLoggingMiddleware(MiddlewareMixin):
    """Middleware to log security-related events"""
    
    def process_request(self, request):
        """Log potential security events"""
        try:
            user = getattr(request, 'user', None)
            ip_address = get_client_ip(request)
            
            # Log failed login attempts (if using Django's built-in auth)
            if request.path == '/admin/login/' and request.method == 'POST':
                if not user or not user.is_authenticated:
                    logger.warning(
                        f"Failed login attempt - IP: {ip_address}, "
                        f"User-Agent: {request.META.get('HTTP_USER_AGENT', 'Unknown')}"
                    )
            
            # Log access to sensitive areas
            sensitive_paths = ['/admin/', '/api/']
            if any(request.path.startswith(path) for path in sensitive_paths):
                if not user or not user.is_authenticated:
                    logger.warning(
                        f"Unauthorized access attempt - Path: {request.path}, "
                        f"IP: {ip_address}, User-Agent: {request.META.get('HTTP_USER_AGENT', 'Unknown')}"
                    )
            
        except Exception as e:
            logger.error(f"Error in security logging middleware: {str(e)}")
        
        return None
