from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import (
    Category, Location, Vendor, Device, Software, SoftwareInstallation,
    MaintenanceRecord, NetworkDevice, Computer, Peripheral, InventoryAudit, AuditItem
)
from django.utils import timezone


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'device_count', 'created_at']
    search_fields = ['name', 'description']
    ordering = ['name']

    def device_count(self, obj):
        return obj.devices.count()
    device_count.short_description = 'Devices'


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ['name', 'building', 'floor', 'room', 'device_count', 'created_at']
    list_filter = ['building', 'floor']
    search_fields = ['name', 'building', 'room', 'address']
    ordering = ['name']

    def device_count(self, obj):
        return obj.devices.count()
    device_count.short_description = 'Devices'


@admin.register(Vendor)
class VendorAdmin(admin.ModelAdmin):
    list_display = ['name', 'contact_person', 'email', 'phone', 'device_count', 'created_at']
    list_filter = ['created_at']
    search_fields = ['name', 'contact_person', 'email']
    ordering = ['name']

    def device_count(self, obj):
        return obj.devices.count()
    device_count.short_description = 'Devices'


class SoftwareInstallationInline(admin.TabularInline):
    model = SoftwareInstallation
    extra = 1
    autocomplete_fields = ['software']


class MaintenanceRecordInline(admin.TabularInline):
    model = MaintenanceRecord
    extra = 1
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    list_display = [
        'asset_tag', 'model', 'category', 'status', 'condition', 
        'location', 'assigned_to', 'warranty_status', 'maintenance_status'
    ]
    list_filter = [
        'status', 'condition', 'category', 'location', 'vendor',
        'purchase_date', 'warranty_expiry', 'created_at'
    ]
    search_fields = ['asset_tag', 'serial_number', 'model', 'notes']
    autocomplete_fields = ['category', 'vendor', 'location', 'assigned_to']
    readonly_fields = ['created_at', 'updated_at', 'last_maintenance', 'next_maintenance']
    fieldsets = (
        ('Basic Information', {
            'fields': ('asset_tag', 'serial_number', 'model', 'category', 'vendor')
        }),
        ('Status & Condition', {
            'fields': ('status', 'condition')
        }),
        ('Location & Assignment', {
            'fields': ('location', 'assigned_to')
        }),
        ('Specifications', {
            'fields': ('specifications', 'purchase_date', 'warranty_expiry', 'purchase_price')
        }),
        ('Additional Information', {
            'fields': ('notes', 'image')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'last_maintenance', 'next_maintenance'),
            'classes': ('collapse',)
        }),
    )
    inlines = [SoftwareInstallationInline, MaintenanceRecordInline]

    def warranty_status(self, obj):
        if obj.is_under_warranty():
            return format_html('<span style="color: green;">✓ Under Warranty</span>')
        elif obj.warranty_expiry:
            return format_html('<span style="color: red;">✗ Expired</span>')
        return format_html('<span style="color: gray;">- No Warranty</span>')
    warranty_status.short_description = 'Warranty'

    def maintenance_status(self, obj):
        if obj.needs_maintenance():
            return format_html('<span style="color: orange;">⚠ Needs Maintenance</span>')
        return format_html('<span style="color: green;">✓ OK</span>')
    maintenance_status.short_description = 'Maintenance'


@admin.register(NetworkDevice)
class NetworkDeviceAdmin(DeviceAdmin):
    list_display = DeviceAdmin.list_display + ['ip_address', 'hostname', 'is_managed']
    list_filter = DeviceAdmin.list_filter + ['is_managed', 'network_segment']
    search_fields = DeviceAdmin.search_fields + ['ip_address', 'mac_address', 'hostname']
    
    fieldsets = DeviceAdmin.fieldsets + (
        ('Network Information', {
            'fields': ('ip_address', 'mac_address', 'hostname', 'network_segment', 'is_managed', 'management_ip')
        }),
    )


@admin.register(Computer)
class ComputerAdmin(DeviceAdmin):
    list_display = DeviceAdmin.list_display + ['computer_type', 'operating_system', 'hostname']
    list_filter = DeviceAdmin.list_filter + ['computer_type', 'operating_system', 'domain_joined']
    search_fields = DeviceAdmin.search_fields + ['hostname', 'ip_address', 'mac_address', 'processor']
    
    fieldsets = DeviceAdmin.fieldsets + (
        ('Computer Information', {
            'fields': ('computer_type', 'operating_system', 'os_version', 'processor', 'memory_gb', 'storage_gb')
        }),
        ('Network Information', {
            'fields': ('hostname', 'ip_address', 'mac_address', 'domain_joined', 'domain_name')
        }),
    )


@admin.register(Peripheral)
class PeripheralAdmin(DeviceAdmin):
    list_display = DeviceAdmin.list_display + ['peripheral_type', 'connected_to']
    list_filter = DeviceAdmin.list_filter + ['peripheral_type']
    search_fields = DeviceAdmin.search_fields + ['peripheral_type']
    autocomplete_fields = DeviceAdmin.autocomplete_fields + ['connected_to']
    
    fieldsets = DeviceAdmin.fieldsets + (
        ('Peripheral Information', {
            'fields': ('peripheral_type', 'connected_to')
        }),
    )


@admin.register(Software)
class SoftwareAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'version', 'vendor', 'license_type', 'seats', 'used_seats', 
        'available_seats', 'license_status', 'purchase_date'
    ]
    list_filter = ['license_type', 'vendor', 'purchase_date', 'license_expiry', 'created_at']
    search_fields = ['name', 'version', 'license_key', 'notes']
    autocomplete_fields = ['vendor']
    readonly_fields = ['created_at', 'updated_at', 'used_seats']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'version', 'vendor')
        }),
        ('License Information', {
            'fields': ('license_type', 'license_key', 'license_expiry', 'seats', 'used_seats')
        }),
        ('Purchase Information', {
            'fields': ('purchase_date', 'purchase_price')
        }),
        ('Additional Information', {
            'fields': ('notes', 'created_at', 'updated_at')
        }),
    )

    def available_seats(self, obj):
        return obj.available_seats()
    available_seats.short_description = 'Available Seats'

    def license_status(self, obj):
        if obj.is_expired():
            return format_html('<span style="color: red;">✗ Expired</span>')
        elif obj.license_expiry:
            return format_html('<span style="color: green;">✓ Active</span>')
        return format_html('<span style="color: gray;">- No Expiry</span>')
    license_status.short_description = 'License Status'


@admin.register(SoftwareInstallation)
class SoftwareInstallationAdmin(admin.ModelAdmin):
    list_display = ['device', 'software', 'installed_by', 'installed_date']
    list_filter = ['installed_date', 'software', 'device__category']
    search_fields = ['device__asset_tag', 'software__name', 'notes']
    autocomplete_fields = ['device', 'software', 'installed_by']
    readonly_fields = ['installed_date']


@admin.register(MaintenanceRecord)
class MaintenanceRecordAdmin(admin.ModelAdmin):
    list_display = [
        'device', 'maintenance_type', 'performed_by', 'scheduled_date', 
        'performed_date', 'cost', 'status'
    ]
    list_filter = [
        'maintenance_type', 'performed_date', 'scheduled_date', 
        'device__category', 'vendor', 'created_at'
    ]
    search_fields = ['device__asset_tag', 'description', 'parts_used', 'notes']
    autocomplete_fields = ['device', 'performed_by', 'vendor']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Device Information', {
            'fields': ('device', 'maintenance_type')
        }),
        ('Maintenance Details', {
            'fields': ('description', 'performed_by', 'vendor')
        }),
        ('Schedule & Performance', {
            'fields': ('scheduled_date', 'performed_date')
        }),
        ('Cost & Parts', {
            'fields': ('cost', 'parts_used')
        }),
        ('Additional Information', {
            'fields': ('notes', 'created_at', 'updated_at')
        }),
    )

    def status(self, obj):
        if obj.performed_date:
            return format_html('<span style="color: green;">✓ Completed</span>')
        elif obj.scheduled_date and obj.scheduled_date < timezone.now():
            return format_html('<span style="color: red;">⚠ Overdue</span>')
        elif obj.scheduled_date:
            return format_html('<span style="color: blue;">📅 Scheduled</span>')
        return format_html('<span style="color: gray;">- Pending</span>')
    status.short_description = 'Status'


class AuditItemInline(admin.TabularInline):
    model = AuditItem
    extra = 1
    autocomplete_fields = ['device', 'expected_location', 'actual_location']


@admin.register(InventoryAudit)
class InventoryAuditAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'audit_type', 'conducted_by', 'start_date', 'end_date', 
        'item_count', 'completion_status'
    ]
    list_filter = ['audit_type', 'start_date', 'end_date', 'conducted_by']
    search_fields = ['title', 'description', 'findings', 'recommendations']
    autocomplete_fields = ['conducted_by']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [AuditItemInline]
    
    fieldsets = (
        ('Audit Information', {
            'fields': ('title', 'audit_type', 'description', 'conducted_by')
        }),
        ('Schedule', {
            'fields': ('start_date', 'end_date')
        }),
        ('Results', {
            'fields': ('findings', 'recommendations')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def item_count(self, obj):
        return obj.audit_items.count()
    item_count.short_description = 'Items'

    def completion_status(self, obj):
        if obj.end_date:
            return format_html('<span style="color: green;">✓ Completed</span>')
        elif obj.start_date and obj.start_date < timezone.now():
            return format_html('<span style="color: orange;">🔄 In Progress</span>')
        return format_html('<span style="color: blue;">📅 Scheduled</span>')
    completion_status.short_description = 'Status'


@admin.register(AuditItem)
class AuditItemAdmin(admin.ModelAdmin):
    list_display = [
        'audit', 'device', 'expected_location', 'actual_location', 
        'found', 'condition', 'audited_at'
    ]
    list_filter = ['found', 'condition', 'audited_at', 'audit__audit_type']
    search_fields = ['device__asset_tag', 'audit__title', 'notes']
    autocomplete_fields = ['audit', 'device', 'expected_location', 'actual_location']
    readonly_fields = ['audited_at']


# Customize admin site
admin.site.site_header = "IT Inventory Management System"
admin.site.site_title = "IT Inventory Admin"
admin.site.index_title = "Welcome to IT Inventory Management"
