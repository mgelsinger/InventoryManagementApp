#!/usr/bin/env python3
"""
Setup script for IT Inventory Management System
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path


def run_command(command, description):
    """Run a command and handle errors"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        print(f"Error output: {e.stderr}")
        return False


def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        print(f"Current version: {sys.version}")
        return False
    print(f"✅ Python version {sys.version.split()[0]} is compatible")
    return True


def create_env_file():
    """Create .env file if it doesn't exist"""
    env_file = Path('.env')
    if not env_file.exists():
        print("📝 Creating .env file...")
        env_content = """SECRET_KEY=django-insecure-change-this-in-production
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
"""
        with open(env_file, 'w') as f:
            f.write(env_content)
        print("✅ .env file created")
    else:
        print("✅ .env file already exists")


def create_directories():
    """Create necessary directories"""
    directories = ['media', 'static', 'staticfiles']
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
    print("✅ Directories created")


def main():
    """Main setup function"""
    print("🚀 IT Inventory Management System Setup")
    print("=" * 50)
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Create virtual environment
    if not Path('venv').exists():
        if not run_command('python -m venv venv', 'Creating virtual environment'):
            sys.exit(1)
    else:
        print("✅ Virtual environment already exists")
    
    # Set up virtual environment paths
    if os.name == 'nt':  # Windows
        python_cmd = 'venv\\Scripts\\python.exe'
        pip_cmd = 'venv\\Scripts\\pip.exe'
    else:  # Unix/Linux/macOS
        python_cmd = 'venv/bin/python'
        pip_cmd = 'venv/bin/pip'
    
    # Install requirements
    if not run_command(f'{pip_cmd} install -r requirements.txt', 'Installing dependencies'):
        sys.exit(1)
    
    # Create .env file
    create_env_file()
    
    # Create directories
    create_directories()
    
    # Run migrations
    if not run_command(f'{python_cmd} manage.py makemigrations', 'Creating database migrations'):
        sys.exit(1)
    
    if not run_command(f'{python_cmd} manage.py migrate', 'Applying database migrations'):
        sys.exit(1)
    
    # Create superuser
    print("👤 Creating superuser account...")
    print("Please enter the following information for the admin account:")
    
    # Collect superuser information
    username = input("Username (default: admin): ").strip() or 'admin'
    email = input("Email: ").strip()
    password = input("Password: ").strip()
    
    if not password:
        print("❌ Password is required")
        sys.exit(1)
    
    # Create superuser using Django management command
    create_superuser_cmd = f'{python_cmd} manage.py shell -c "from django.contrib.auth.models import User; User.objects.create_superuser(\'{username}\', \'{email}\', \'{password}\')"'
    
    if not run_command(create_superuser_cmd, 'Creating superuser'):
        print("⚠️  Failed to create superuser automatically. You can create it manually later.")
    
    # Collect static files
    if not run_command(f'{python_cmd} manage.py collectstatic --noinput', 'Collecting static files'):
        print("⚠️  Static files collection failed, but you can continue")
    
    print("\n" + "=" * 50)
    print("🎉 Setup completed successfully!")
    print("\nNext steps:")
    print("1. Start the development server:")
    print("   python manage.py runserver")
    print("\n2. Access the application:")
    print("   Web interface: http://127.0.0.1:8000/")
    print("   Admin panel: http://127.0.0.1:8000/admin/")
    print("\n3. Log in with your superuser credentials")
    print("\n4. Start adding categories, locations, vendors, and devices")
    print("\nFor more information, see the README.md file")


if __name__ == '__main__':
    main()
