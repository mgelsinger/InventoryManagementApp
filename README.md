# IT Inventory Management System

A comprehensive Django-based inventory management system designed specifically for IT departments to track and manage hardware, software, maintenance, and related assets.

## Features

### 🖥️ Device Management
- **Hardware Tracking**: Monitor computers, servers, network devices, and peripherals
- **Asset Lifecycle**: Track from purchase to retirement with warranty and maintenance schedules
- **Location Management**: Assign devices to specific locations, buildings, floors, and rooms
- **User Assignment**: Track which devices are assigned to which users
- **Condition Monitoring**: Track device condition (excellent, good, fair, poor, broken)
- **Specifications**: Store detailed technical specifications as JSON data

### 💾 Software Management
- **License Tracking**: Monitor software licenses, expiry dates, and seat usage
- **Vendor Management**: Track software vendors and contact information
- **Installation Records**: Track which software is installed on which devices
- **License Types**: Support for perpetual, subscription, trial, and open-source licenses
- **Expiry Alerts**: Automatic tracking of expiring licenses

### 🔧 Maintenance Management
- **Scheduled Maintenance**: Plan and track preventive maintenance schedules
- **Maintenance Records**: Detailed records of all maintenance activities
- **Cost Tracking**: Monitor maintenance costs and parts used
- **Vendor Integration**: Track maintenance performed by external vendors
- **Status Tracking**: Monitor pending, overdue, and completed maintenance

### 📊 Dashboard & Reporting
- **Real-time Statistics**: Overview of total devices, active devices, maintenance needs
- **Status Breakdown**: Visual representation of device status distribution
- **Recent Activity**: Track recent devices and maintenance activities
- **Export Functionality**: Export device data to CSV format
- **Search & Filter**: Advanced search and filtering capabilities

### 🔐 Security & Access Control
- **User Authentication**: Secure login system
- **Role-based Access**: Different access levels for different users
- **Audit Trails**: Track changes and modifications
- **Data Validation**: Comprehensive form validation and data integrity checks

### 🌐 API Support
- **REST API**: Full REST API for integration with other systems
- **JSON Serialization**: Complete API serialization for all models
- **Filtering & Search**: API endpoints support filtering and search
- **Authentication**: API authentication and permission controls

## Technology Stack

- **Backend**: Django 4.2.7 (Python 3.x)
- **Database**: SQLite (configurable for PostgreSQL/MySQL)
- **Frontend**: Bootstrap 5, jQuery
- **API**: Django REST Framework
- **Tables**: django-tables2 for sortable, filterable tables
- **Forms**: django-crispy-forms with Bootstrap 5 styling
- **Filtering**: django-filter for advanced filtering

## Installation

### Prerequisites
- Python 3.8 or higher
- pip (Python package installer)

### Step 1: Clone the Repository
```bash
git clone <repository-url>
cd it-inventory-system
```

### Step 2: Create Virtual Environment
```bash
python -m venv venv

# On Windows
venv\Scripts\activate

# On macOS/Linux
source venv/bin/activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Configure Environment Variables
Create a `.env` file in the project root:
```env
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
```

### Step 5: Run Database Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### Step 6: Create Superuser
```bash
python manage.py createsuperuser
```

### Step 7: Run the Development Server
```bash
python manage.py runserver
```

The application will be available at `http://127.0.0.1:8000/`

## Usage

### Initial Setup

1. **Access Admin Panel**: Go to `http://127.0.0.1:8000/admin/` and log in with your superuser credentials

2. **Create Categories**: Add device categories (e.g., Desktop, Laptop, Server, Network Device)

3. **Add Locations**: Create locations for your devices (buildings, floors, rooms)

4. **Add Vendors**: Enter vendor information for your equipment and software

5. **Add Devices**: Start adding your IT equipment with asset tags and specifications

### Managing Devices

1. **Add New Device**: Use the "Add Device" button on the dashboard or device list
2. **Assign Location**: Set the physical location of the device
3. **Assign User**: Link devices to specific users if applicable
4. **Track Maintenance**: Schedule and record maintenance activities
5. **Monitor Status**: Update device status as needed (active, maintenance, retired)

### Software Management

1. **Add Software**: Enter software details including license information
2. **Track Licenses**: Monitor license expiry dates and seat usage
3. **Record Installations**: Track which devices have which software installed
4. **Monitor Expiry**: Get alerts for expiring licenses

### Maintenance Tracking

1. **Schedule Maintenance**: Plan preventive maintenance schedules
2. **Record Activities**: Document all maintenance activities with costs and parts
3. **Track Vendors**: Record maintenance performed by external vendors
4. **Monitor Status**: Track pending, overdue, and completed maintenance

## API Usage

The system provides a comprehensive REST API for integration:

### Authentication
```bash
# Include authentication header in API requests
Authorization: Token your-token-here
```

### Example API Endpoints

```bash
# Get all devices
GET /api/devices/

# Get specific device
GET /api/devices/{id}/

# Create new device
POST /api/devices/

# Get devices needing maintenance
GET /api/devices/needs_maintenance/

# Get dashboard statistics
GET /api/dashboard/stats/
```

### API Documentation
Full API documentation is available at `/api/` when running the development server.

## Configuration

### Database Configuration
The default configuration uses SQLite. For production, update `settings.py`:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'your_db_name',
        'USER': 'your_db_user',
        'PASSWORD': 'your_db_password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

### Static Files
For production, configure static file serving:

```bash
python manage.py collectstatic
```

### Email Configuration
Configure email settings for notifications:

```python
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'your-smtp-server'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'your-email@domain.com'
EMAIL_HOST_PASSWORD = 'your-password'
```

## Customization

### Adding Custom Fields
To add custom fields to devices, modify the `Device` model in `inventory/models.py`:

```python
class Device(models.Model):
    # ... existing fields ...
    custom_field = models.CharField(max_length=100, blank=True)
```

### Custom Reports
Create custom reports by adding new views and templates:

```python
# In views.py
@login_required
def custom_report(request):
    # Your custom report logic
    return render(request, 'inventory/custom_report.html', context)
```

### Custom Filters
Add custom filters by extending the filter classes in `filters.py`:

```python
class CustomDeviceFilter(DeviceFilter):
    custom_field = CharFilter(lookup_expr='icontains')
```

## Troubleshooting

### Common Issues

1. **Migration Errors**: If you encounter migration errors, try:
   ```bash
   python manage.py migrate --fake-initial
   ```

2. **Static Files Not Loading**: Ensure you've run:
   ```bash
   python manage.py collectstatic
   ```

3. **Permission Errors**: Check file permissions for media uploads:
   ```bash
   chmod 755 media/
   ```

### Debug Mode
For development, ensure `DEBUG=True` in your `.env` file. For production, set `DEBUG=False`.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions:
- Create an issue in the repository
- Check the documentation
- Review the Django documentation for general Django questions

## Roadmap

- [ ] Barcode/QR code generation for devices
- [ ] Mobile app for inventory scanning
- [ ] Advanced reporting and analytics
- [ ] Integration with procurement systems
- [ ] Automated backup and restore functionality
- [ ] Multi-tenant support
- [ ] Advanced notification system
- [ ] Asset depreciation tracking
- [ ] Integration with monitoring systems
