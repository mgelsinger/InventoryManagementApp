from rest_framework import serializers
from django.contrib.auth.models import User
from .models import (
    Device, Category, Location, Vendor, Software, MaintenanceRecord,
    NetworkDevice, Computer, Peripheral, SoftwareInstallation
)
from django.utils import timezone


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model"""
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email', 'full_name']
        read_only_fields = ['id']
    
    def get_full_name(self, obj):
        return obj.get_full_name() or obj.username


class CategorySerializer(serializers.ModelSerializer):
    """Serializer for Category model"""
    device_count = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Category
        fields = ['id', 'name', 'description', 'device_count', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class LocationSerializer(serializers.ModelSerializer):
    """Serializer for Location model"""
    device_count = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Location
        fields = ['id', 'name', 'building', 'floor', 'room', 'address', 'description', 'device_count', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class VendorSerializer(serializers.ModelSerializer):
    """Serializer for Vendor model"""
    device_count = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Vendor
        fields = ['id', 'name', 'contact_person', 'email', 'phone', 'website', 'address', 'device_count', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class DeviceSerializer(serializers.ModelSerializer):
    """Serializer for Device model"""
    category = CategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(),
        source='category',
        write_only=True
    )
    vendor = VendorSerializer(read_only=True)
    vendor_id = serializers.PrimaryKeyRelatedField(
        queryset=Vendor.objects.all(),
        source='vendor',
        write_only=True,
        required=False,
        allow_null=True
    )
    location = LocationSerializer(read_only=True)
    location_id = serializers.PrimaryKeyRelatedField(
        queryset=Location.objects.all(),
        source='location',
        write_only=True,
        required=False,
        allow_null=True
    )
    assigned_to = UserSerializer(read_only=True)
    assigned_to_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        source='assigned_to',
        write_only=True,
        required=False,
        allow_null=True
    )
    warranty_status = serializers.SerializerMethodField()
    maintenance_status = serializers.SerializerMethodField()
    
    class Meta:
        model = Device
        fields = [
            'id', 'asset_tag', 'serial_number', 'model', 'category', 'category_id',
            'vendor', 'vendor_id', 'status', 'condition', 'location', 'location_id',
            'assigned_to', 'assigned_to_id', 'specifications', 'purchase_date',
            'warranty_expiry', 'purchase_price', 'notes', 'image', 'created_at',
            'updated_at', 'last_maintenance', 'next_maintenance', 'warranty_status',
            'maintenance_status'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'last_maintenance', 'next_maintenance']
    
    def get_warranty_status(self, obj):
        if obj.is_under_warranty():
            return 'under_warranty'
        elif obj.warranty_expiry:
            return 'expired'
        return 'no_warranty'
    
    def get_maintenance_status(self, obj):
        if obj.needs_maintenance():
            return 'needs_maintenance'
        return 'ok'


class NetworkDeviceSerializer(DeviceSerializer):
    """Serializer for NetworkDevice model"""
    
    class Meta(DeviceSerializer.Meta):
        model = NetworkDevice
        fields = DeviceSerializer.Meta.fields + [
            'ip_address', 'mac_address', 'hostname', 'network_segment',
            'is_managed', 'management_ip'
        ]


class ComputerSerializer(DeviceSerializer):
    """Serializer for Computer model"""
    
    class Meta(DeviceSerializer.Meta):
        model = Computer
        fields = DeviceSerializer.Meta.fields + [
            'computer_type', 'operating_system', 'os_version', 'processor',
            'memory_gb', 'storage_gb', 'hostname', 'ip_address', 'mac_address',
            'domain_joined', 'domain_name'
        ]


class PeripheralSerializer(DeviceSerializer):
    """Serializer for Peripheral model"""
    connected_to = ComputerSerializer(read_only=True)
    connected_to_id = serializers.PrimaryKeyRelatedField(
        queryset=Computer.objects.all(),
        source='connected_to',
        write_only=True,
        required=False,
        allow_null=True
    )
    
    class Meta(DeviceSerializer.Meta):
        model = Peripheral
        fields = DeviceSerializer.Meta.fields + ['peripheral_type', 'connected_to', 'connected_to_id']


class SoftwareSerializer(serializers.ModelSerializer):
    """Serializer for Software model"""
    vendor = VendorSerializer(read_only=True)
    vendor_id = serializers.PrimaryKeyRelatedField(
        queryset=Vendor.objects.all(),
        source='vendor',
        write_only=True,
        required=False,
        allow_null=True
    )
    available_seats = serializers.SerializerMethodField()
    license_status = serializers.SerializerMethodField()
    
    class Meta:
        model = Software
        fields = [
            'id', 'name', 'version', 'vendor', 'vendor_id', 'license_type',
            'license_key', 'license_expiry', 'seats', 'used_seats', 'available_seats',
            'purchase_date', 'purchase_price', 'notes', 'created_at', 'updated_at',
            'license_status'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'used_seats']
    
    def get_available_seats(self, obj):
        return obj.available_seats()
    
    def get_license_status(self, obj):
        if obj.is_expired():
            return 'expired'
        elif obj.license_expiry:
            return 'active'
        return 'no_expiry'


class SoftwareInstallationSerializer(serializers.ModelSerializer):
    """Serializer for SoftwareInstallation model"""
    device = DeviceSerializer(read_only=True)
    device_id = serializers.PrimaryKeyRelatedField(
        queryset=Device.objects.all(),
        source='device',
        write_only=True
    )
    software = SoftwareSerializer(read_only=True)
    software_id = serializers.PrimaryKeyRelatedField(
        queryset=Software.objects.all(),
        source='software',
        write_only=True
    )
    installed_by = UserSerializer(read_only=True)
    
    class Meta:
        model = SoftwareInstallation
        fields = [
            'id', 'device', 'device_id', 'software', 'software_id',
            'installed_by', 'installed_date', 'notes'
        ]
        read_only_fields = ['id', 'installed_by', 'installed_date']


class MaintenanceRecordSerializer(serializers.ModelSerializer):
    """Serializer for MaintenanceRecord model"""
    device = DeviceSerializer(read_only=True)
    device_id = serializers.PrimaryKeyRelatedField(
        queryset=Device.objects.all(),
        source='device',
        write_only=True
    )
    performed_by = UserSerializer(read_only=True)
    performed_by_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        source='performed_by',
        write_only=True,
        required=False,
        allow_null=True
    )
    vendor = VendorSerializer(read_only=True)
    vendor_id = serializers.PrimaryKeyRelatedField(
        queryset=Vendor.objects.all(),
        source='vendor',
        write_only=True,
        required=False,
        allow_null=True
    )
    status = serializers.SerializerMethodField()
    
    class Meta:
        model = MaintenanceRecord
        fields = [
            'id', 'device', 'device_id', 'maintenance_type', 'description',
            'performed_by', 'performed_by_id', 'vendor', 'vendor_id',
            'scheduled_date', 'performed_date', 'cost', 'parts_used', 'notes',
            'created_at', 'updated_at', 'status'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_status(self, obj):
        if obj.performed_date:
            return 'completed'
        elif obj.scheduled_date and obj.scheduled_date < timezone.now():
            return 'overdue'
        elif obj.scheduled_date:
            return 'scheduled'
        return 'pending'


# Nested serializers for detailed views
class DeviceDetailSerializer(DeviceSerializer):
    """Detailed serializer for Device with related data"""
    software_installations = SoftwareInstallationSerializer(many=True, read_only=True)
    maintenance_records = MaintenanceRecordSerializer(many=True, read_only=True)
    
    class Meta(DeviceSerializer.Meta):
        fields = DeviceSerializer.Meta.fields + ['software_installations', 'maintenance_records']


class SoftwareDetailSerializer(SoftwareSerializer):
    """Detailed serializer for Software with installations"""
    installations = SoftwareInstallationSerializer(many=True, read_only=True)
    
    class Meta(SoftwareSerializer.Meta):
        fields = SoftwareSerializer.Meta.fields + ['installations']


# Dashboard serializers
class DashboardStatsSerializer(serializers.Serializer):
    """Serializer for dashboard statistics"""
    total_devices = serializers.IntegerField()
    active_devices = serializers.IntegerField()
    devices_needing_maintenance = serializers.IntegerField()
    devices_under_warranty = serializers.IntegerField()
    total_software = serializers.IntegerField()
    expiring_licenses = serializers.IntegerField()
    expired_licenses = serializers.IntegerField()
    pending_maintenance = serializers.IntegerField()


class RecentActivitySerializer(serializers.Serializer):
    """Serializer for recent activity"""
    recent_devices = DeviceSerializer(many=True)
    recent_maintenance = MaintenanceRecordSerializer(many=True)
