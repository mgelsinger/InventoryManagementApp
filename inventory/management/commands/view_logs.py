from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
import os
import re
from datetime import datetime, timedelta
from collections import defaultdict, Counter


class Command(BaseCommand):
    help = 'View and analyze application logs'

    def add_arguments(self, parser):
        parser.add_argument(
            '--log-file',
            type=str,
            help='Specific log file to analyze (general, errors, security, database, api)'
        )
        parser.add_argument(
            '--level',
            type=str,
            choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
            help='Filter by log level'
        )
        parser.add_argument(
            '--user',
            type=str,
            help='Filter by username'
        )
        parser.add_argument(
            '--ip',
            type=str,
            help='Filter by IP address'
        )
        parser.add_argument(
            '--hours',
            type=int,
            default=24,
            help='Show logs from last N hours (default: 24)'
        )
        parser.add_argument(
            '--summary',
            action='store_true',
            help='Show summary statistics instead of detailed logs'
        )
        parser.add_argument(
            '--errors-only',
            action='store_true',
            help='Show only error logs'
        )
        parser.add_argument(
            '--top-users',
            type=int,
            default=10,
            help='Show top N users by activity (for summary mode)'
        )
        parser.add_argument(
            '--top-ips',
            type=int,
            default=10,
            help='Show top N IP addresses by activity (for summary mode)'
        )

    def handle(self, *args, **options):
        try:
            logs_dir = os.path.join(settings.BASE_DIR, 'logs')
            
            if not os.path.exists(logs_dir):
                self.stdout.write(
                    self.style.ERROR(f'Logs directory not found: {logs_dir}')
                )
                return

            # Determine which log files to analyze
            if options['log_file']:
                log_files = [f"{options['log_file']}.log"]
            else:
                log_files = ['general.log', 'errors.log', 'security.log', 'database.log', 'api.log']

            # Filter logs based on options
            filtered_logs = self.filter_logs(logs_dir, log_files, options)
            
            if options['summary']:
                self.show_summary(filtered_logs, options)
            else:
                self.show_detailed_logs(filtered_logs, options)

        except Exception as e:
            raise CommandError(f'Error analyzing logs: {str(e)}')

    def filter_logs(self, logs_dir, log_files, options):
        """Filter logs based on command options"""
        filtered_logs = []
        cutoff_time = datetime.now() - timedelta(hours=options['hours'])
        
        for log_file in log_files:
            log_path = os.path.join(logs_dir, log_file)
            if not os.path.exists(log_path):
                continue
                
            with open(log_path, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        # Parse log line
                        log_entry = self.parse_log_line(line)
                        if not log_entry:
                            continue
                            
                        # Apply filters
                        if self.should_include_log(log_entry, options, cutoff_time):
                            filtered_logs.append(log_entry)
                            
                    except Exception as e:
                        # Skip malformed log lines
                        continue
        
        return filtered_logs

    def parse_log_line(self, line):
        """Parse a log line and extract relevant information"""
        try:
            # Match the detailed format: [timestamp] LEVEL name funcName:line - message
            pattern = r'\[(.*?)\] (\w+) (\w+) (\w+):(\d+) - (.*)'
            match = re.match(pattern, line.strip())
            
            if match:
                timestamp_str, level, name, func_name, line_num, message = match.groups()
                timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S,%f')
                
                return {
                    'timestamp': timestamp,
                    'level': level,
                    'name': name,
                    'func_name': func_name,
                    'line_num': int(line_num),
                    'message': message,
                    'raw_line': line.strip()
                }
            
            return None
            
        except Exception:
            return None

    def should_include_log(self, log_entry, options, cutoff_time):
        """Check if log entry should be included based on filters"""
        # Time filter
        if log_entry['timestamp'] < cutoff_time:
            return False
            
        # Level filter
        if options['level'] and log_entry['level'] != options['level']:
            return False
            
        # User filter
        if options['user']:
            user_pattern = re.compile(rf"User: .*{options['user']}.*", re.IGNORECASE)
            if not user_pattern.search(log_entry['message']):
                return False
                
        # IP filter
        if options['ip']:
            ip_pattern = re.compile(rf"IP: {options['ip']}", re.IGNORECASE)
            if not ip_pattern.search(log_entry['message']):
                return False
                
        # Errors only filter
        if options['errors_only'] and log_entry['level'] != 'ERROR':
            return False
            
        return True

    def show_detailed_logs(self, logs, options):
        """Show detailed log entries"""
        if not logs:
            self.stdout.write(self.style.WARNING('No logs found matching the criteria.'))
            return
            
        self.stdout.write(f"\nShowing {len(logs)} log entries:\n")
        
        for log in logs:
            timestamp = log['timestamp'].strftime('%Y-%m-%d %H:%M:%S')
            level_color = self.get_level_color(log['level'])
            
            self.stdout.write(
                f"{level_color}[{timestamp}] {log['level']} - {log['message']}"
            )

    def show_summary(self, logs, options):
        """Show summary statistics"""
        if not logs:
            self.stdout.write(self.style.WARNING('No logs found matching the criteria.'))
            return
            
        self.stdout.write(f"\nLog Summary (Last {options['hours']} hours):\n")
        self.stdout.write("=" * 50)
        
        # Level distribution
        level_counts = Counter(log['level'] for log in logs)
        self.stdout.write("\nLog Levels:")
        for level, count in level_counts.most_common():
            level_color = self.get_level_color(level)
            self.stdout.write(f"  {level_color}{level}: {count}")
        
        # Top users
        user_counts = self.extract_user_counts(logs)
        if user_counts:
            self.stdout.write(f"\nTop {options['top_users']} Users:")
            for user, count in user_counts.most_common(options['top_users']):
                self.stdout.write(f"  {user}: {count} actions")
        
        # Top IP addresses
        ip_counts = self.extract_ip_counts(logs)
        if ip_counts:
            self.stdout.write(f"\nTop {options['top_ips']} IP Addresses:")
            for ip, count in ip_counts.most_common(options['top_ips']):
                self.stdout.write(f"  {ip}: {count} requests")
        
        # Error analysis
        error_logs = [log for log in logs if log['level'] == 'ERROR']
        if error_logs:
            self.stdout.write(f"\nError Analysis ({len(error_logs)} errors):")
            error_patterns = Counter()
            for log in error_logs:
                # Extract error type from message
                error_type = self.extract_error_type(log['message'])
                error_patterns[error_type] += 1
            
            for error_type, count in error_patterns.most_common(5):
                self.stdout.write(f"  {error_type}: {count} occurrences")

    def extract_user_counts(self, logs):
        """Extract user activity counts from logs"""
        user_counts = Counter()
        for log in logs:
            # Look for user patterns in messages
            user_match = re.search(r'User: ([^(]+)', log['message'])
            if user_match:
                user = user_match.group(1).strip()
                user_counts[user] += 1
        return user_counts

    def extract_ip_counts(self, logs):
        """Extract IP address counts from logs"""
        ip_counts = Counter()
        for log in logs:
            # Look for IP patterns in messages
            ip_match = re.search(r'IP: ([^\s,]+)', log['message'])
            if ip_match:
                ip = ip_match.group(1)
                ip_counts[ip] += 1
        return ip_counts

    def extract_error_type(self, message):
        """Extract error type from error message"""
        # Try to extract meaningful error type
        if 'Database' in message:
            return 'Database Error'
        elif 'API' in message:
            return 'API Error'
        elif 'View' in message:
            return 'View Error'
        elif 'Middleware' in message:
            return 'Middleware Error'
        else:
            return 'General Error'

    def get_level_color(self, level):
        """Get color for log level"""
        if level == 'ERROR':
            return self.style.ERROR('')
        elif level == 'WARNING':
            return self.style.WARNING('')
        elif level == 'INFO':
            return self.style.SUCCESS('')
        else:
            return ''
