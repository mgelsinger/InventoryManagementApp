import logging
import traceback
from functools import wraps
from django.contrib.auth.models import User
from django.http import HttpRequest
from typing import Any, Dict, Optional, Callable

# Get loggers for different components
logger = logging.getLogger('inventory')
api_logger = logging.getLogger('inventory.api')
db_logger = logging.getLogger('inventory.models')
view_logger = logging.getLogger('inventory.views')


def log_function_call(func: Callable) -> Callable:
    """Decorator to log function calls with parameters and results"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        func_name = func.__name__
        module_name = func.__module__
        
        try:
            # Log function entry
            logger.info(f"Function called: {module_name}.{func_name}")
            
            # Execute function
            result = func(*args, **kwargs)
            
            # Log successful completion
            logger.info(f"Function completed successfully: {module_name}.{func_name}")
            return result
            
        except Exception as e:
            # Log error with full traceback
            logger.error(f"Function failed: {module_name}.{func_name} - Error: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise
    
    return wrapper


def log_user_action(user: User, action: str, details: str = "", request: Optional[HttpRequest] = None):
    """Log user actions for audit purposes"""
    try:
        user_info = f"{user.username} (ID: {user.id})"
        ip_address = get_client_ip(request) if request else "Unknown"
        
        log_message = f"User Action - User: {user_info}, Action: {action}, IP: {ip_address}"
        if details:
            log_message += f", Details: {details}"
        
        logger.info(log_message)
        
    except Exception as e:
        logger.error(f"Failed to log user action: {str(e)}")


def log_api_request(request: HttpRequest, response_data: Any = None, error: Optional[Exception] = None):
    """Log API requests and responses"""
    try:
        user = getattr(request, 'user', None)
        user_info = f"{user.username} (ID: {user.id})" if user and user.is_authenticated else "Anonymous"
        ip_address = get_client_ip(request)
        method = request.method
        path = request.path
        status_code = getattr(request, 'status_code', 'Unknown')
        
        if error:
            api_logger.error(
                f"API Error - Method: {method}, Path: {path}, User: {user_info}, "
                f"IP: {ip_address}, Status: {status_code}, Error: {str(error)}"
            )
        else:
            api_logger.info(
                f"API Request - Method: {method}, Path: {path}, User: {user_info}, "
                f"IP: {ip_address}, Status: {status_code}"
            )
            
    except Exception as e:
        logger.error(f"Failed to log API request: {str(e)}")


def log_database_operation(operation: str, model: str, record_id: Optional[int] = None, 
                          user: Optional[User] = None, details: str = ""):
    """Log database operations"""
    try:
        user_info = f"{user.username} (ID: {user.id})" if user else "System"
        record_info = f" (ID: {record_id})" if record_id else ""
        
        log_message = f"Database Operation - Operation: {operation}, Model: {model}{record_info}, User: {user_info}"
        if details:
            log_message += f", Details: {details}"
        
        db_logger.info(log_message)
        
    except Exception as e:
        logger.error(f"Failed to log database operation: {str(e)}")


def log_security_event(event_type: str, user: Optional[User] = None, 
                      request: Optional[HttpRequest] = None, details: str = ""):
    """Log security-related events"""
    try:
        security_logger = logging.getLogger('django.security')
        
        user_info = f"{user.username} (ID: {user.id})" if user else "Unknown"
        ip_address = get_client_ip(request) if request else "Unknown"
        
        log_message = f"Security Event - Type: {event_type}, User: {user_info}, IP: {ip_address}"
        if details:
            log_message += f", Details: {details}"
        
        security_logger.warning(log_message)
        
    except Exception as e:
        logger.error(f"Failed to log security event: {str(e)}")


def log_error(error: Exception, context: str = "", user: Optional[User] = None, 
             request: Optional[HttpRequest] = None):
    """Log errors with context information"""
    try:
        user_info = f"{user.username} (ID: {user.id})" if user else "Unknown"
        ip_address = get_client_ip(request) if request else "Unknown"
        
        error_message = f"Error in {context} - User: {user_info}, IP: {ip_address}, Error: {str(error)}"
        error_message += f"\nTraceback: {traceback.format_exc()}"
        
        logger.error(error_message)
        
    except Exception as e:
        logger.error(f"Failed to log error: {str(e)}")


def log_view_access(view_name: str, request: HttpRequest, response_time: float = None):
    """Log view access for monitoring"""
    try:
        user = getattr(request, 'user', None)
        user_info = f"{user.username} (ID: {user.id})" if user and user.is_authenticated else "Anonymous"
        ip_address = get_client_ip(request)
        method = request.method
        
        log_message = f"View Access - View: {view_name}, Method: {method}, User: {user_info}, IP: {ip_address}"
        if response_time:
            log_message += f", Response Time: {response_time:.3f}s"
        
        view_logger.info(log_message)
        
    except Exception as e:
        logger.error(f"Failed to log view access: {str(e)}")


def get_client_ip(request: HttpRequest) -> str:
    """Extract client IP address from request"""
    try:
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip or "Unknown"
    except Exception:
        return "Unknown"


def log_model_operation(operation: str, model_instance: Any, user: Optional[User] = None):
    """Log model operations (create, update, delete)"""
    try:
        model_name = model_instance.__class__.__name__
        record_id = getattr(model_instance, 'id', None)
        
        log_database_operation(
            operation=operation,
            model=model_name,
            record_id=record_id,
            user=user,
            details=f"Operation performed on {model_name}"
        )
        
    except Exception as e:
        logger.error(f"Failed to log model operation: {str(e)}")


def log_bulk_operation(operation: str, model: str, count: int, user: Optional[User] = None):
    """Log bulk operations"""
    try:
        log_database_operation(
            operation=operation,
            model=model,
            user=user,
            details=f"Bulk operation affecting {count} records"
        )
        
    except Exception as e:
        logger.error(f"Failed to log bulk operation: {str(e)}")


def log_export_operation(export_type: str, user: User, record_count: int, format: str = "csv"):
    """Log data export operations"""
    try:
        log_message = f"Data Export - Type: {export_type}, Format: {format}, Records: {record_count}, User: {user.username}"
        logger.info(log_message)
        
    except Exception as e:
        logger.error(f"Failed to log export operation: {str(e)}")


def log_import_operation(import_type: str, user: User, record_count: int, success_count: int, error_count: int = 0):
    """Log data import operations"""
    try:
        log_message = f"Data Import - Type: {import_type}, Total: {record_count}, Success: {success_count}, Errors: {error_count}, User: {user.username}"
        logger.info(log_message)
        
    except Exception as e:
        logger.error(f"Failed to log import operation: {str(e)}")


def log_maintenance_event(device_id: int, maintenance_type: str, user: User, details: str = ""):
    """Log maintenance events"""
    try:
        log_message = f"Maintenance Event - Device ID: {device_id}, Type: {maintenance_type}, User: {user.username}"
        if details:
            log_message += f", Details: {details}"
        
        logger.info(log_message)
        
    except Exception as e:
        logger.error(f"Failed to log maintenance event: {str(e)}")


def log_software_installation(device_id: int, software_name: str, user: User):
    """Log software installation events"""
    try:
        log_message = f"Software Installation - Device ID: {device_id}, Software: {software_name}, User: {user.username}"
        logger.info(log_message)
        
    except Exception as e:
        logger.error(f"Failed to log software installation: {str(e)}")


def log_audit_event(audit_type: str, user: User, items_count: int, findings: str = ""):
    """Log audit events"""
    try:
        log_message = f"Audit Event - Type: {audit_type}, User: {user.username}, Items: {items_count}"
        if findings:
            log_message += f", Findings: {findings}"
        
        logger.info(log_message)
        
    except Exception as e:
        logger.error(f"Failed to log audit event: {str(e)}")
