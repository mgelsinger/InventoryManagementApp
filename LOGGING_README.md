# IT Inventory Management System - Logging System

## Overview

The IT Inventory Management System includes a comprehensive logging system that captures all application activities, errors, and security events. This system provides detailed audit trails, performance monitoring, and debugging capabilities.

## Log Files Structure

The logging system creates the following log files in the `logs/` directory:

### 1. `general.log`
- **Purpose**: General application logs, user actions, and system events
- **Level**: INFO and above
- **Content**: Dashboard access, device operations, user actions, view access
- **Rotation**: 5MB max size, 5 backup files

### 2. `errors.log`
- **Purpose**: Error and exception logging
- **Level**: ERROR only
- **Content**: Application errors, exceptions, failed operations
- **Rotation**: 5MB max size, 5 backup files

### 3. `security.log`
- **Purpose**: Security-related events
- **Level**: WARNING and above
- **Content**: Failed login attempts, unauthorized access, security violations
- **Rotation**: 5MB max size, 5 backup files

### 4. `database.log`
- **Purpose**: Database operations and queries
- **Level**: DEBUG and above
- **Content**: SQL queries, model operations, database performance
- **Rotation**: 5MB max size, 5 backup files

### 5. `api.log`
- **Purpose**: API request and response logging
- **Level**: INFO and above
- **Content**: API calls, responses, performance metrics
- **Rotation**: 5MB max size, 5 backup files

## Log Format

All logs use a detailed format for easy parsing and analysis:

```
[2025-08-15 21:19:24,865] INFO inventory.views dashboard:45 - Dashboard accessed by user: admin
```

**Format**: `[timestamp] LEVEL module function:line - message`

## Logging Components

### 1. Logging Configuration (`settings.py`)

The logging system is configured in Django settings with:
- Multiple handlers for different log types
- Rotating file handlers with size limits
- Different log levels for different components
- Formatters for consistent log structure

### 2. Logging Utilities (`inventory/logging_utils.py`)

Provides convenient functions for logging:

#### Core Functions:
- `log_user_action()` - Log user activities
- `log_api_request()` - Log API requests and responses
- `log_database_operation()` - Log database operations
- `log_security_event()` - Log security events
- `log_error()` - Log errors with context
- `log_view_access()` - Log view access with timing

#### Specialized Functions:
- `log_model_operation()` - Log model CRUD operations
- `log_bulk_operation()` - Log bulk operations
- `log_export_operation()` - Log data exports
- `log_import_operation()` - Log data imports
- `log_maintenance_event()` - Log maintenance activities
- `log_software_installation()` - Log software installations
- `log_audit_event()` - Log audit activities

### 3. Middleware (`inventory/middleware.py`)

#### RequestLoggingMiddleware
- Automatically logs all HTTP requests and responses
- Captures timing information
- Logs exceptions and errors
- Skips static/media files to reduce noise

#### SecurityLoggingMiddleware
- Logs failed login attempts
- Logs unauthorized access to sensitive areas
- Captures security-related events

### 4. Model Signal Logging

Automatic logging of model operations through Django signals:
- Logs CREATE, UPDATE, and DELETE operations
- Captures model name and record ID
- Provides audit trail for all data changes

## Management Commands

### 1. View Logs (`view_logs`)

Analyze and filter logs with various options:

```bash
# View summary of last 24 hours
python manage.py view_logs --summary

# View errors only
python manage.py view_logs --errors-only

# Filter by user
python manage.py view_logs --user admin

# Filter by IP address
python manage.py view_logs --ip 127.0.0.1

# View specific log file
python manage.py view_logs --log-file errors

# View logs from last 48 hours
python manage.py view_logs --hours 48

# Show top 20 users by activity
python manage.py view_logs --summary --top-users 20
```

### 2. Cleanup Logs (`cleanup_logs`)

Manage log file rotation and cleanup:

```bash
# Clean up logs older than 30 days
python manage.py cleanup_logs --days 30

# Rotate logs larger than 50MB
python manage.py cleanup_logs --max-size 50

# Dry run to see what would be deleted
python manage.py cleanup_logs --dry-run

# Compress old backup files
python manage.py cleanup_logs --compress

# Keep only 3 backup files
python manage.py cleanup_logs --backup-count 3
```

## Logged Events

### User Actions
- Dashboard access
- Device creation, updates, deletion
- Software management
- Maintenance scheduling
- Data exports and imports
- API usage

### System Events
- Database operations
- File uploads/downloads
- Email notifications
- Background tasks
- System errors and exceptions

### Security Events
- Failed login attempts
- Unauthorized access attempts
- Permission violations
- Suspicious activities

### Performance Metrics
- Request response times
- Database query performance
- API response times
- File operation timing

## Try-Catch Implementation

The logging system includes comprehensive error handling with try-catch blocks in:

### Views
- All view functions have try-catch blocks
- Errors are logged with context information
- User-friendly error messages are displayed
- Performance timing is captured

### API Views
- All API endpoints have error handling
- Request and response logging
- Error details are captured
- User action tracking

### Models
- Signal handlers have error handling
- Database operation logging
- Model lifecycle tracking

### Middleware
- Request processing errors
- Response generation errors
- Exception handling

## Best Practices

### 1. Log Levels
- **DEBUG**: Detailed information for debugging
- **INFO**: General application flow
- **WARNING**: Potential issues that don't stop execution
- **ERROR**: Errors that need attention

### 2. Log Messages
- Use descriptive, actionable messages
- Include relevant context (user, IP, operation)
- Avoid logging sensitive information
- Use consistent formatting

### 3. Performance
- Log files are rotated to prevent disk space issues
- Static files are excluded from request logging
- Database logging can be disabled in production
- Log compression reduces storage requirements

### 4. Security
- IP addresses are logged for security analysis
- User actions are tracked for audit purposes
- Failed login attempts are monitored
- Sensitive data is not logged

## Monitoring and Alerting

### 1. Error Monitoring
- Monitor `errors.log` for application errors
- Set up alerts for high error rates
- Track error patterns and trends

### 2. Performance Monitoring
- Monitor response times in logs
- Track database query performance
- Identify slow operations

### 3. Security Monitoring
- Monitor `security.log` for security events
- Track failed login attempts
- Monitor unauthorized access attempts

### 4. User Activity Monitoring
- Track user actions and patterns
- Monitor API usage
- Identify unusual activity

## Troubleshooting

### Common Issues

1. **Log files not created**
   - Check if `logs/` directory exists
   - Verify write permissions
   - Check Django logging configuration

2. **Large log files**
   - Run log cleanup command
   - Adjust rotation settings
   - Compress old logs

3. **Missing log entries**
   - Check log level settings
   - Verify logger configuration
   - Check for exceptions in logging code

### Debugging Commands

```bash
# Check log file sizes
ls -lh logs/

# View recent errors
python manage.py view_logs --errors-only --hours 1

# Check for specific user activity
python manage.py view_logs --user admin --hours 24

# Analyze log patterns
python manage.py view_logs --summary --hours 168  # Last week
```

## Integration with External Tools

The logging system can be integrated with external monitoring tools:

### 1. Log Aggregation
- Send logs to centralized logging systems
- Use tools like ELK Stack, Splunk, or Graylog
- Implement log forwarding for real-time monitoring

### 2. Monitoring Systems
- Integrate with monitoring tools like Nagios, Zabbix
- Set up alerts based on log patterns
- Monitor application health through logs

### 3. Security Information and Event Management (SIEM)
- Forward security logs to SIEM systems
- Implement real-time security monitoring
- Set up automated threat detection

## Future Enhancements

1. **Structured Logging**: Implement JSON logging for better parsing
2. **Log Analytics**: Add built-in log analysis dashboard
3. **Real-time Monitoring**: Implement real-time log streaming
4. **Advanced Filtering**: Add more sophisticated log filtering options
5. **Log Retention Policies**: Implement automated log retention management
6. **Performance Metrics**: Add detailed performance monitoring
7. **Security Analytics**: Implement advanced security event analysis

## Conclusion

The logging system provides comprehensive visibility into the IT Inventory Management System's operation, security, and performance. It enables effective monitoring, debugging, and audit capabilities while maintaining good performance and security practices.
