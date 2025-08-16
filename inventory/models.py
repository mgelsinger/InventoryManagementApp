from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
import uuid
import logging

# Get logger for models
logger = logging.getLogger('inventory.models')


class Category(models.Model):
    """Model for IT equipment categories"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['name']

    def __str__(self):
        return self.name


class Location(models.Model):
    """Model for physical locations"""
    name = models.CharField(max_length=100)
    building = models.CharField(max_length=100, blank=True)
    floor = models.CharField(max_length=20, blank=True)
    room = models.CharField(max_length=50, blank=True)
    address = models.TextField(blank=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} - {self.building} {self.room}".strip()


class Vendor(models.Model):
    """Model for equipment vendors"""
    name = models.CharField(max_length=200, unique=True)
    contact_person = models.CharField(max_length=100, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    website = models.URLField(blank=True)
    address = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Device(models.Model):
    """Model for IT devices/equipment"""
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('maintenance', 'Under Maintenance'),
        ('retired', 'Retired'),
        ('lost', 'Lost/Stolen'),
    ]

    CONDITION_CHOICES = [
        ('excellent', 'Excellent'),
        ('good', 'Good'),
        ('fair', 'Fair'),
        ('poor', 'Poor'),
        ('broken', 'Broken'),
    ]

    # Basic Information
    asset_tag = models.CharField(max_length=50, unique=True, help_text="Unique asset identifier")
    serial_number = models.CharField(max_length=100, blank=True, help_text="Device serial number")
    model = models.CharField(max_length=200)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='devices')
    vendor = models.ForeignKey(Vendor, on_delete=models.SET_NULL, null=True, blank=True, related_name='devices')
    
    # Status and Condition
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    condition = models.CharField(max_length=20, choices=CONDITION_CHOICES, default='good')
    
    # Location and Assignment
    location = models.ForeignKey(Location, on_delete=models.SET_NULL, null=True, blank=True, related_name='devices')
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_devices')
    
    # Specifications
    specifications = models.JSONField(default=dict, blank=True, help_text="Technical specifications as JSON")
    purchase_date = models.DateField(null=True, blank=True)
    warranty_expiry = models.DateField(null=True, blank=True)
    purchase_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Additional Information
    notes = models.TextField(blank=True)
    image = models.ImageField(upload_to='device_images/', blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_maintenance = models.DateTimeField(null=True, blank=True)
    next_maintenance = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['asset_tag']

    def __str__(self):
        return f"{self.asset_tag} - {self.model}"

    def is_under_warranty(self):
        if self.warranty_expiry:
            return self.warranty_expiry > timezone.now().date()
        return False

    def needs_maintenance(self):
        if self.next_maintenance:
            return self.next_maintenance <= timezone.now()
        return False


class Software(models.Model):
    """Model for software licenses and installations"""
    LICENSE_TYPES = [
        ('perpetual', 'Perpetual'),
        ('subscription', 'Subscription'),
        ('trial', 'Trial'),
        ('open_source', 'Open Source'),
    ]

    name = models.CharField(max_length=200)
    version = models.CharField(max_length=50, blank=True)
    vendor = models.ForeignKey(Vendor, on_delete=models.SET_NULL, null=True, blank=True, related_name='software')
    license_type = models.CharField(max_length=20, choices=LICENSE_TYPES, default='perpetual')
    license_key = models.CharField(max_length=200, blank=True)
    license_expiry = models.DateField(null=True, blank=True)
    seats = models.PositiveIntegerField(default=1, help_text="Number of licenses/seats")
    used_seats = models.PositiveIntegerField(default=0)
    purchase_date = models.DateField(null=True, blank=True)
    purchase_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        verbose_name_plural = "Software"

    def __str__(self):
        return f"{self.name} v{self.version}" if self.version else self.name

    def available_seats(self):
        return self.seats - self.used_seats

    def is_expired(self):
        if self.license_expiry:
            return self.license_expiry < timezone.now().date()
        return False


class SoftwareInstallation(models.Model):
    """Model for software installations on devices"""
    device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name='software_installations')
    software = models.ForeignKey(Software, on_delete=models.CASCADE, related_name='installations')
    installed_date = models.DateTimeField(auto_now_add=True)
    installed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        unique_together = ['device', 'software']
        ordering = ['-installed_date']

    def __str__(self):
        return f"{self.software.name} on {self.device.asset_tag}"


class MaintenanceRecord(models.Model):
    """Model for maintenance and repair records"""
    MAINTENANCE_TYPES = [
        ('preventive', 'Preventive Maintenance'),
        ('corrective', 'Corrective Maintenance'),
        ('upgrade', 'Upgrade'),
        ('inspection', 'Inspection'),
    ]

    device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name='maintenance_records')
    maintenance_type = models.CharField(max_length=20, choices=MAINTENANCE_TYPES)
    description = models.TextField()
    performed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    vendor = models.ForeignKey(Vendor, on_delete=models.SET_NULL, null=True, blank=True)
    scheduled_date = models.DateTimeField(null=True, blank=True)
    performed_date = models.DateTimeField(null=True, blank=True)
    cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    parts_used = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-performed_date', '-scheduled_date']

    def __str__(self):
        return f"{self.device.asset_tag} - {self.maintenance_type} - {self.performed_date}"


class NetworkDevice(Device):
    """Model for network-specific devices"""
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    mac_address = models.CharField(max_length=17, blank=True)
    hostname = models.CharField(max_length=100, blank=True)
    network_segment = models.CharField(max_length=50, blank=True)
    is_managed = models.BooleanField(default=False)
    management_ip = models.GenericIPAddressField(blank=True, null=True)

    class Meta:
        verbose_name = "Network Device"
        verbose_name_plural = "Network Devices"

    def __str__(self):
        return f"{self.asset_tag} - {self.hostname or self.ip_address}"


class Computer(Device):
    """Model for computers and workstations"""
    COMPUTER_TYPES = [
        ('desktop', 'Desktop'),
        ('laptop', 'Laptop'),
        ('server', 'Server'),
        ('workstation', 'Workstation'),
        ('thin_client', 'Thin Client'),
    ]

    computer_type = models.CharField(max_length=20, choices=COMPUTER_TYPES, default='desktop')
    operating_system = models.CharField(max_length=100, blank=True)
    os_version = models.CharField(max_length=50, blank=True)
    processor = models.CharField(max_length=100, blank=True)
    memory_gb = models.PositiveIntegerField(blank=True, null=True)
    storage_gb = models.PositiveIntegerField(blank=True, null=True)
    hostname = models.CharField(max_length=100, blank=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    mac_address = models.CharField(max_length=17, blank=True)
    domain_joined = models.BooleanField(default=False)
    domain_name = models.CharField(max_length=100, blank=True)

    class Meta:
        verbose_name = "Computer"
        verbose_name_plural = "Computers"

    def __str__(self):
        return f"{self.asset_tag} - {self.hostname or self.model}"


class Peripheral(Device):
    """Model for peripherals and accessories"""
    PERIPHERAL_TYPES = [
        ('monitor', 'Monitor'),
        ('keyboard', 'Keyboard'),
        ('mouse', 'Mouse'),
        ('printer', 'Printer'),
        ('scanner', 'Scanner'),
        ('speaker', 'Speaker'),
        ('headset', 'Headset'),
        ('webcam', 'Webcam'),
        ('other', 'Other'),
    ]

    peripheral_type = models.CharField(max_length=20, choices=PERIPHERAL_TYPES, default='other')
    connected_to = models.ForeignKey(Computer, on_delete=models.SET_NULL, null=True, blank=True, related_name='peripherals')

    class Meta:
        verbose_name = "Peripheral"
        verbose_name_plural = "Peripherals"

    def __str__(self):
        return f"{self.asset_tag} - {self.get_peripheral_type_display()}"


class InventoryAudit(models.Model):
    """Model for inventory audit records"""
    AUDIT_TYPES = [
        ('physical', 'Physical Audit'),
        ('system', 'System Audit'),
        ('compliance', 'Compliance Audit'),
    ]

    audit_type = models.CharField(max_length=20, choices=AUDIT_TYPES)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    conducted_by = models.ForeignKey(User, on_delete=models.CASCADE)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField(null=True, blank=True)
    findings = models.TextField(blank=True)
    recommendations = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-start_date']

    def __str__(self):
        return f"{self.title} - {self.start_date.date()}"


class AuditItem(models.Model):
    """Model for individual items in an audit"""
    audit = models.ForeignKey(InventoryAudit, on_delete=models.CASCADE, related_name='audit_items')
    device = models.ForeignKey(Device, on_delete=models.CASCADE)
    expected_location = models.ForeignKey(Location, on_delete=models.SET_NULL, null=True, blank=True)
    actual_location = models.ForeignKey(Location, on_delete=models.SET_NULL, null=True, blank=True, related_name='audit_findings')
    found = models.BooleanField(default=False)
    condition = models.CharField(max_length=20, choices=Device.CONDITION_CHOICES, blank=True)
    notes = models.TextField(blank=True)
    audited_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['audit', 'device']
        ordering = ['audited_at']

    def __str__(self):
        return f"{self.audit.title} - {self.device.asset_tag}"


# Signal handlers for logging model operations
@receiver(post_save)
def log_model_save(sender, instance, created, **kwargs):
    """Log model save operations"""
    try:
        if sender.__module__.startswith('inventory'):
            operation = "CREATE" if created else "UPDATE"
            model_name = sender.__name__
            record_id = getattr(instance, 'id', None)
            
            logger.info(f"Model {operation} - {model_name} (ID: {record_id})")
    except Exception as e:
        logger.error(f"Failed to log model save: {str(e)}")


@receiver(post_delete)
def log_model_delete(sender, instance, **kwargs):
    """Log model delete operations"""
    try:
        if sender.__module__.startswith('inventory'):
            model_name = sender.__name__
            record_id = getattr(instance, 'id', None)
            
            logger.info(f"Model DELETE - {model_name} (ID: {record_id})")
    except Exception as e:
        logger.error(f"Failed to log model delete: {str(e)}")
