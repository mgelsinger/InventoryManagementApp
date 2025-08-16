from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
import os
import glob
from datetime import datetime, timedelta
import shutil


class Command(BaseCommand):
    help = 'Clean up old log files and manage log rotation'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='Delete log files older than N days (default: 30)'
        )
        parser.add_argument(
            '--max-size',
            type=int,
            default=50,
            help='Maximum log file size in MB (default: 50)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually deleting'
        )
        parser.add_argument(
            '--compress',
            action='store_true',
            help='Compress old log files instead of deleting them'
        )
        parser.add_argument(
            '--backup-count',
            type=int,
            default=5,
            help='Number of backup files to keep (default: 5)'
        )

    def handle(self, *args, **options):
        try:
            logs_dir = os.path.join(settings.BASE_DIR, 'logs')
            
            if not os.path.exists(logs_dir):
                self.stdout.write(
                    self.style.WARNING(f'Logs directory not found: {logs_dir}')
                )
                return

            self.stdout.write(f'Cleaning up logs in: {logs_dir}')
            
            # Clean up old log files
            deleted_count = self.cleanup_old_logs(logs_dir, options)
            
            # Rotate large log files
            rotated_count = self.rotate_large_logs(logs_dir, options)
            
            # Compress old backups if requested
            compressed_count = 0
            if options['compress']:
                compressed_count = self.compress_old_backups(logs_dir, options)
            
            # Summary
            self.stdout.write(f'\nCleanup Summary:')
            self.stdout.write(f'  Deleted files: {deleted_count}')
            self.stdout.write(f'  Rotated files: {rotated_count}')
            if options['compress']:
                self.stdout.write(f'  Compressed files: {compressed_count}')
            
            self.stdout.write(
                self.style.SUCCESS('Log cleanup completed successfully!')
            )

        except Exception as e:
            raise CommandError(f'Error during log cleanup: {str(e)}')

    def cleanup_old_logs(self, logs_dir, options):
        """Delete log files older than specified days"""
        cutoff_date = datetime.now() - timedelta(days=options['days'])
        deleted_count = 0
        
        # Find all log files
        log_patterns = ['*.log', '*.log.*']
        all_log_files = []
        
        for pattern in log_patterns:
            all_log_files.extend(glob.glob(os.path.join(logs_dir, pattern)))
        
        for log_file in all_log_files:
            try:
                file_stat = os.stat(log_file)
                file_date = datetime.fromtimestamp(file_stat.st_mtime)
                
                if file_date < cutoff_date:
                    if options['dry_run']:
                        self.stdout.write(f'Would delete: {os.path.basename(log_file)}')
                    else:
                        os.remove(log_file)
                        self.stdout.write(f'Deleted: {os.path.basename(log_file)}')
                    deleted_count += 1
                    
            except Exception as e:
                self.stdout.write(
                    self.style.WARNING(f'Error processing {log_file}: {str(e)}')
                )
        
        return deleted_count

    def rotate_large_logs(self, logs_dir, options):
        """Rotate log files that exceed the maximum size"""
        max_size_bytes = options['max_size'] * 1024 * 1024  # Convert MB to bytes
        rotated_count = 0
        
        # Find current log files (not backups)
        current_logs = glob.glob(os.path.join(logs_dir, '*.log'))
        
        for log_file in current_logs:
            try:
                file_size = os.path.getsize(log_file)
                
                if file_size > max_size_bytes:
                    if options['dry_run']:
                        self.stdout.write(f'Would rotate: {os.path.basename(log_file)} ({file_size / 1024 / 1024:.1f} MB)')
                    else:
                        self.rotate_log_file(log_file, options['backup_count'])
                        self.stdout.write(f'Rotated: {os.path.basename(log_file)}')
                    rotated_count += 1
                    
            except Exception as e:
                self.stdout.write(
                    self.style.WARNING(f'Error rotating {log_file}: {str(e)}')
                )
        
        return rotated_count

    def rotate_log_file(self, log_file, backup_count):
        """Rotate a single log file"""
        base_name = os.path.basename(log_file)
        dir_name = os.path.dirname(log_file)
        
        # Remove oldest backup if we have too many
        oldest_backup = os.path.join(dir_name, f'{base_name}.{backup_count}')
        if os.path.exists(oldest_backup):
            os.remove(oldest_backup)
        
        # Shift existing backups
        for i in range(backup_count - 1, 0, -1):
            old_name = os.path.join(dir_name, f'{base_name}.{i}')
            new_name = os.path.join(dir_name, f'{base_name}.{i + 1}')
            if os.path.exists(old_name):
                shutil.move(old_name, new_name)
        
        # Move current log to .1
        backup_name = os.path.join(dir_name, f'{base_name}.1')
        shutil.move(log_file, backup_name)
        
        # Create new empty log file
        open(log_file, 'w').close()

    def compress_old_backups(self, logs_dir, options):
        """Compress old backup log files"""
        import gzip
        compressed_count = 0
        
        # Find backup files (not already compressed)
        backup_patterns = ['*.log.[2-9]', '*.log.1[0-9]']
        backup_files = []
        
        for pattern in backup_patterns:
            backup_files.extend(glob.glob(os.path.join(logs_dir, pattern)))
        
        for backup_file in backup_files:
            try:
                # Skip if already compressed
                if backup_file.endswith('.gz'):
                    continue
                
                compressed_file = f'{backup_file}.gz'
                
                if options['dry_run']:
                    self.stdout.write(f'Would compress: {os.path.basename(backup_file)}')
                else:
                    with open(backup_file, 'rb') as f_in:
                        with gzip.open(compressed_file, 'wb') as f_out:
                            shutil.copyfileobj(f_in, f_out)
                    
                    # Remove original file
                    os.remove(backup_file)
                    self.stdout.write(f'Compressed: {os.path.basename(backup_file)}')
                
                compressed_count += 1
                
            except Exception as e:
                self.stdout.write(
                    self.style.WARNING(f'Error compressing {backup_file}: {str(e)}')
                )
        
        return compressed_count

    def get_file_size_mb(self, file_path):
        """Get file size in MB"""
        try:
            return os.path.getsize(file_path) / 1024 / 1024
        except:
            return 0
