from rest_framework import viewsets, status
from rest_framework.decorators import api_view, action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.db.models import Count, Q
from django.utils import timezone
import logging
from .models import (
    Device, Category, Location, Vendor, Software, MaintenanceRecord,
    NetworkDevice, Computer, Peripheral
)
from .serializers import (
    DeviceSerializer, CategorySerializer, LocationSerializer, VendorSerializer,
    SoftwareSerializer, MaintenanceRecordSerializer, NetworkDeviceSerializer,
    ComputerSerializer, PeripheralSerializer
)
from .logging_utils import log_api_request, log_user_action, log_error

# Get logger for API views
logger = logging.getLogger('inventory.api')


class DeviceViewSet(viewsets.ModelViewSet):
    """ViewSet for Device model"""
    queryset = Device.objects.select_related('category', 'vendor', 'location', 'assigned_to')
    serializer_class = DeviceSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['status', 'condition', 'category', 'vendor', 'location']
    search_fields = ['asset_tag', 'serial_number', 'model', 'notes']
    ordering_fields = ['asset_tag', 'model', 'created_at', 'purchase_date']
    ordering = ['asset_tag']

    def list(self, request, *args, **kwargs):
        try:
            response = super().list(request, *args, **kwargs)
            log_api_request(request, response.data)
            log_user_action(request.user, 'api_device_list', f"Retrieved {len(response.data.get('results', []))} devices")
            return response
        except Exception as e:
            log_api_request(request, error=e)
            log_error(e, 'DeviceViewSet.list', request.user, request)
            raise

    def create(self, request, *args, **kwargs):
        try:
            response = super().create(request, *args, **kwargs)
            log_api_request(request, response.data)
            log_user_action(request.user, 'api_device_create', f"Created device ID: {response.data.get('id')}")
            return response
        except Exception as e:
            log_api_request(request, error=e)
            log_error(e, 'DeviceViewSet.create', request.user, request)
            raise

    def update(self, request, *args, **kwargs):
        try:
            response = super().update(request, *args, **kwargs)
            log_api_request(request, response.data)
            log_user_action(request.user, 'api_device_update', f"Updated device ID: {response.data.get('id')}")
            return response
        except Exception as e:
            log_api_request(request, error=e)
            log_error(e, 'DeviceViewSet.update', request.user, request)
            raise

    def destroy(self, request, *args, **kwargs):
        try:
            device_id = self.get_object().id
            response = super().destroy(request, *args, **kwargs)
            log_api_request(request)
            log_user_action(request.user, 'api_device_delete', f"Deleted device ID: {device_id}")
            return response
        except Exception as e:
            log_api_request(request, error=e)
            log_error(e, 'DeviceViewSet.destroy', request.user, request)
            raise

    @action(detail=True, methods=['post'])
    def mark_maintenance(self, request, pk=None):
        try:
            device = self.get_object()
            device.status = 'maintenance'
            device.save()
            
            log_user_action(request.user, 'api_device_maintenance', f"Marked device {device.asset_tag} for maintenance")
            logger.info(f"Device {device.asset_tag} marked for maintenance via API")
            
            return Response({'status': 'Device marked for maintenance'})
        except Exception as e:
            log_error(e, 'DeviceViewSet.mark_maintenance', request.user, request)
            raise

    @action(detail=True, methods=['post'])
    def mark_active(self, request, pk=None):
        try:
            device = self.get_object()
            device.status = 'active'
            device.save()
            
            log_user_action(request.user, 'api_device_active', f"Marked device {device.asset_tag} as active")
            logger.info(f"Device {device.asset_tag} marked as active via API")
            
            return Response({'status': 'Device marked as active'})
        except Exception as e:
            log_error(e, 'DeviceViewSet.mark_active', request.user, request)
            raise

    @action(detail=False, methods=['get'])
    def needs_maintenance(self, request):
        try:
            devices = self.get_queryset().filter(next_maintenance__lte=timezone.now())
            serializer = self.get_serializer(devices, many=True)
            
            log_user_action(request.user, 'api_devices_maintenance_check', f"Found {len(devices)} devices needing maintenance")
            logger.info(f"API request for devices needing maintenance - {len(devices)} found")
            
            return Response(serializer.data)
        except Exception as e:
            log_error(e, 'DeviceViewSet.needs_maintenance', request.user, request)
            raise

    @action(detail=False, methods=['get'])
    def under_warranty(self, request):
        try:
            devices = self.get_queryset().filter(warranty_expiry__gt=timezone.now().date())
            serializer = self.get_serializer(devices, many=True)
            
            log_user_action(request.user, 'api_devices_warranty_check', f"Found {len(devices)} devices under warranty")
            logger.info(f"API request for devices under warranty - {len(devices)} found")
            
            return Response(serializer.data)
        except Exception as e:
            log_error(e, 'DeviceViewSet.under_warranty', request.user, request)
            raise


class NetworkDeviceViewSet(DeviceViewSet):
    """ViewSet for NetworkDevice model"""
    queryset = NetworkDevice.objects.select_related('category', 'vendor', 'location', 'assigned_to')
    serializer_class = NetworkDeviceSerializer
    filterset_fields = DeviceViewSet.filterset_fields + ['is_managed', 'network_segment']
    search_fields = DeviceViewSet.search_fields + ['ip_address', 'hostname', 'mac_address']


class ComputerViewSet(DeviceViewSet):
    """ViewSet for Computer model"""
    queryset = Computer.objects.select_related('category', 'vendor', 'location', 'assigned_to')
    serializer_class = ComputerSerializer
    filterset_fields = DeviceViewSet.filterset_fields + ['computer_type', 'operating_system', 'domain_joined']
    search_fields = DeviceViewSet.search_fields + ['hostname', 'ip_address', 'mac_address', 'processor']


class PeripheralViewSet(DeviceViewSet):
    """ViewSet for Peripheral model"""
    queryset = Peripheral.objects.select_related('category', 'vendor', 'location', 'assigned_to', 'connected_to')
    serializer_class = PeripheralSerializer
    filterset_fields = DeviceViewSet.filterset_fields + ['peripheral_type', 'connected_to']


class SoftwareViewSet(viewsets.ModelViewSet):
    """ViewSet for Software model"""
    queryset = Software.objects.select_related('vendor')
    serializer_class = SoftwareSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['license_type', 'vendor']
    search_fields = ['name', 'version', 'license_key']
    ordering_fields = ['name', 'version', 'purchase_date', 'license_expiry']
    ordering = ['name']

    @action(detail=False, methods=['get'])
    def expiring_soon(self, request):
        from datetime import timedelta
        future_date = timezone.now().date() + timedelta(days=30)
        software = self.get_queryset().filter(
            license_expiry__lte=future_date,
            license_expiry__gt=timezone.now().date()
        )
        serializer = self.get_serializer(software, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def expired(self, request):
        software = self.get_queryset().filter(license_expiry__lt=timezone.now().date())
        serializer = self.get_serializer(software, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def low_seats(self, request):
        software = self.get_queryset().filter(used_seats__gte=Q('seats') - 2)
        serializer = self.get_serializer(software, many=True)
        return Response(serializer.data)


class MaintenanceRecordViewSet(viewsets.ModelViewSet):
    """ViewSet for MaintenanceRecord model"""
    queryset = MaintenanceRecord.objects.select_related('device', 'performed_by', 'vendor')
    serializer_class = MaintenanceRecordSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['maintenance_type', 'device', 'performed_by', 'vendor']
    search_fields = ['description', 'parts_used', 'notes']
    ordering_fields = ['scheduled_date', 'performed_date', 'created_at']
    ordering = ['-performed_date', '-scheduled_date']

    @action(detail=False, methods=['get'])
    def pending(self, request):
        records = self.get_queryset().filter(performed_date__isnull=True)
        serializer = self.get_serializer(records, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def overdue(self, request):
        records = self.get_queryset().filter(
            performed_date__isnull=True,
            scheduled_date__lt=timezone.now()
        )
        serializer = self.get_serializer(records, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def completed(self, request):
        records = self.get_queryset().filter(performed_date__isnull=False)
        serializer = self.get_serializer(records, many=True)
        return Response(serializer.data)


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for Category model (read-only)"""
    queryset = Category.objects.annotate(device_count=Count('devices'))
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'device_count']
    ordering = ['name']


class LocationViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for Location model (read-only)"""
    queryset = Location.objects.annotate(device_count=Count('devices'))
    serializer_class = LocationSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['name', 'building', 'room', 'address']
    ordering_fields = ['name', 'device_count']
    ordering = ['name']


class VendorViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for Vendor model (read-only)"""
    queryset = Vendor.objects.annotate(device_count=Count('devices'))
    serializer_class = VendorSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['name', 'contact_person', 'email']
    ordering_fields = ['name', 'device_count']
    ordering = ['name']


# Legacy API views for backward compatibility
class DeviceListAPIView(DeviceViewSet):
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)


class DeviceDetailAPIView(DeviceViewSet):
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)


class SoftwareListAPIView(SoftwareViewSet):
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)


class SoftwareDetailAPIView(SoftwareViewSet):
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)


class MaintenanceListAPIView(MaintenanceRecordViewSet):
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)


class MaintenanceDetailAPIView(MaintenanceRecordViewSet):
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)


class CategoryListAPIView(CategoryViewSet):
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)


class LocationListAPIView(LocationViewSet):
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)


class VendorListAPIView(VendorViewSet):
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)


@api_view(['GET'])
def dashboard_stats(request):
    """API endpoint for dashboard statistics"""
    try:
        logger.info(f"Dashboard stats API requested by user: {request.user.username}")
        
        today = timezone.now().date()
        
        stats = {
            'total_devices': Device.objects.count(),
            'active_devices': Device.objects.filter(status='active').count(),
            'devices_needing_maintenance': Device.objects.filter(next_maintenance__lte=timezone.now()).count(),
            'devices_under_warranty': Device.objects.filter(warranty_expiry__gt=today).count(),
            'total_software': Software.objects.count(),
            'expiring_licenses': Software.objects.filter(
                license_expiry__lte=today + timezone.timedelta(days=30),
                license_expiry__gt=today
            ).count(),
            'expired_licenses': Software.objects.filter(license_expiry__lt=today).count(),
            'pending_maintenance': MaintenanceRecord.objects.filter(
                performed_date__isnull=True,
                scheduled_date__lte=timezone.now()
            ).count(),
        }
        
        log_api_request(request, stats)
        log_user_action(request.user, 'api_dashboard_stats', f"Retrieved dashboard statistics")
        logger.info(f"Dashboard stats API completed successfully for user: {request.user.username}")
        
        return Response(stats)
        
    except Exception as e:
        log_api_request(request, error=e)
        log_error(e, 'dashboard_stats API', request.user, request)
        logger.error(f"Dashboard stats API failed: {str(e)}")
        return Response({'error': 'Failed to retrieve dashboard statistics'}, status=500)


@api_view(['GET'])
def recent_activity(request):
    """API endpoint for recent activity"""
    recent_devices = Device.objects.order_by('-created_at')[:5]
    recent_maintenance = MaintenanceRecord.objects.order_by('-created_at')[:5]
    
    activity = {
        'recent_devices': DeviceSerializer(recent_devices, many=True).data,
        'recent_maintenance': MaintenanceRecordSerializer(recent_maintenance, many=True).data,
    }
    
    return Response(activity)


class DashboardStatsAPIView(viewsets.ViewSet):
    """ViewSet for dashboard statistics"""
    permission_classes = [IsAuthenticated]

    def list(self, request):
        return dashboard_stats(request)


class RecentActivityAPIView(viewsets.ViewSet):
    """ViewSet for recent activity"""
    permission_classes = [IsAuthenticated]

    def list(self, request):
        return recent_activity(request)
