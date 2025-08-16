import django_filters
from django_filters import CharFilter, ChoiceFilter, DateFilter, NumberFilter
from django.contrib.auth.models import User
from .models import Device, Software, MaintenanceRecord, Category, Location, Vendor, NetworkDevice, Computer, Peripheral


class DeviceFilter(django_filters.FilterSet):
    """Filter for devices"""
    asset_tag = CharFilter(lookup_expr='icontains', label='Asset Tag')
    model = CharFilter(lookup_expr='icontains', label='Model')
    serial_number = CharFilter(lookup_expr='icontains', label='Serial Number')
    category = django_filters.ModelChoiceFilter(queryset=Category.objects.all(), label='Category')
    vendor = django_filters.ModelChoiceFilter(queryset=Vendor.objects.all(), label='Vendor')
    location = django_filters.ModelChoiceFilter(queryset=Location.objects.all(), label='Location')
    status = ChoiceFilter(choices=Device.STATUS_CHOICES, label='Status')
    condition = ChoiceFilter(choices=Device.CONDITION_CHOICES, label='Condition')
    purchase_date_from = DateFilter(field_name='purchase_date', lookup_expr='gte', label='Purchase Date From')
    purchase_date_to = DateFilter(field_name='purchase_date', lookup_expr='lte', label='Purchase Date To')
    warranty_expiry_from = DateFilter(field_name='warranty_expiry', lookup_expr='gte', label='Warranty Expiry From')
    warranty_expiry_to = DateFilter(field_name='warranty_expiry', lookup_expr='lte', label='Warranty Expiry To')
    price_min = NumberFilter(field_name='purchase_price', lookup_expr='gte', label='Min Price')
    price_max = NumberFilter(field_name='purchase_price', lookup_expr='lte', label='Max Price')
    needs_maintenance = django_filters.BooleanFilter(method='filter_needs_maintenance', label='Needs Maintenance')
    under_warranty = django_filters.BooleanFilter(method='filter_under_warranty', label='Under Warranty')

    class Meta:
        model = Device
        fields = {
            'asset_tag': ['exact', 'icontains'],
            'model': ['exact', 'icontains'],
            'serial_number': ['exact', 'icontains'],
            'status': ['exact'],
            'condition': ['exact'],
            'category': ['exact'],
            'vendor': ['exact'],
            'location': ['exact'],
            'assigned_to': ['exact'],
        }

    def filter_needs_maintenance(self, queryset, name, value):
        if value:
            from django.utils import timezone
            return queryset.filter(next_maintenance__lte=timezone.now())
        return queryset

    def filter_under_warranty(self, queryset, name, value):
        if value:
            from django.utils import timezone
            return queryset.filter(warranty_expiry__gt=timezone.now().date())
        return queryset


class SoftwareFilter(django_filters.FilterSet):
    """Filter for software"""
    name = CharFilter(lookup_expr='icontains', label='Software Name')
    version = CharFilter(lookup_expr='icontains', label='Version')
    vendor = django_filters.ModelChoiceFilter(queryset=Vendor.objects.all(), label='Vendor')
    license_type = ChoiceFilter(choices=Software.LICENSE_TYPES, label='License Type')
    license_expiry_from = DateFilter(field_name='license_expiry', lookup_expr='gte', label='License Expiry From')
    license_expiry_to = DateFilter(field_name='license_expiry', lookup_expr='lte', label='License Expiry To')
    seats_min = NumberFilter(field_name='seats', lookup_expr='gte', label='Min Seats')
    seats_max = NumberFilter(field_name='seats', lookup_expr='lte', label='Max Seats')
    price_min = NumberFilter(field_name='purchase_price', lookup_expr='gte', label='Min Price')
    price_max = NumberFilter(field_name='purchase_price', lookup_expr='lte', label='Max Price')
    expiring_soon = django_filters.BooleanFilter(method='filter_expiring_soon', label='Expiring Soon (30 days)')
    expired = django_filters.BooleanFilter(method='filter_expired', label='Expired')
    low_seats = django_filters.BooleanFilter(method='filter_low_seats', label='Low Available Seats')

    class Meta:
        model = Software
        fields = {
            'name': ['exact', 'icontains'],
            'version': ['exact', 'icontains'],
            'license_type': ['exact'],
            'vendor': ['exact'],
            'seats': ['exact', 'gte', 'lte'],
            'used_seats': ['exact', 'gte', 'lte'],
        }

    def filter_expiring_soon(self, queryset, name, value):
        if value:
            from django.utils import timezone
            from datetime import timedelta
            future_date = timezone.now().date() + timedelta(days=30)
            return queryset.filter(
                license_expiry__lte=future_date,
                license_expiry__gt=timezone.now().date()
            )
        return queryset

    def filter_expired(self, queryset, name, value):
        if value:
            from django.utils import timezone
            return queryset.filter(license_expiry__lt=timezone.now().date())
        return queryset

    def filter_low_seats(self, queryset, name, value):
        if value:
            import django.db.models
            return queryset.filter(used_seats__gte=django.db.models.F('seats') - 2)
        return queryset


class MaintenanceFilter(django_filters.FilterSet):
    """Filter for maintenance records"""
    device = django_filters.ModelChoiceFilter(queryset=Device.objects.all(), label='Device')
    maintenance_type = ChoiceFilter(choices=MaintenanceRecord.MAINTENANCE_TYPES, label='Maintenance Type')
    performed_by = django_filters.ModelChoiceFilter(queryset=User.objects.all(), label='Performed By')
    vendor = django_filters.ModelChoiceFilter(queryset=Vendor.objects.all(), label='Vendor')
    scheduled_date_from = DateFilter(field_name='scheduled_date', lookup_expr='gte', label='Scheduled From')
    scheduled_date_to = DateFilter(field_name='scheduled_date', lookup_expr='lte', label='Scheduled To')
    performed_date_from = DateFilter(field_name='performed_date', lookup_expr='gte', label='Performed From')
    performed_date_to = DateFilter(field_name='performed_date', lookup_expr='lte', label='Performed To')
    cost_min = NumberFilter(field_name='cost', lookup_expr='gte', label='Min Cost')
    cost_max = NumberFilter(field_name='cost', lookup_expr='lte', label='Max Cost')
    pending = django_filters.BooleanFilter(method='filter_pending', label='Pending')
    overdue = django_filters.BooleanFilter(method='filter_overdue', label='Overdue')
    completed = django_filters.BooleanFilter(method='filter_completed', label='Completed')

    class Meta:
        model = MaintenanceRecord
        fields = {
            'maintenance_type': ['exact'],
            'device': ['exact'],
            'performed_by': ['exact'],
            'vendor': ['exact'],
            'cost': ['exact', 'gte', 'lte'],
        }

    def filter_pending(self, queryset, name, value):
        if value:
            return queryset.filter(performed_date__isnull=True)
        return queryset

    def filter_overdue(self, queryset, name, value):
        if value:
            from django.utils import timezone
            return queryset.filter(
                performed_date__isnull=True,
                scheduled_date__lt=timezone.now()
            )
        return queryset

    def filter_completed(self, queryset, name, value):
        if value:
            return queryset.filter(performed_date__isnull=False)
        return queryset


class NetworkDeviceFilter(DeviceFilter):
    """Filter for network devices"""
    ip_address = CharFilter(lookup_expr='icontains', label='IP Address')
    hostname = CharFilter(lookup_expr='icontains', label='Hostname')
    network_segment = CharFilter(lookup_expr='icontains', label='Network Segment')
    is_managed = django_filters.BooleanFilter(label='Managed Device')

    class Meta(DeviceFilter.Meta):
        model = NetworkDevice
        fields = DeviceFilter.Meta.fields | {
            'ip_address': ['exact', 'icontains'],
            'hostname': ['exact', 'icontains'],
            'network_segment': ['exact', 'icontains'],
            'is_managed': ['exact'],
        }


class ComputerFilter(DeviceFilter):
    """Filter for computers"""
    computer_type = ChoiceFilter(choices=Computer.COMPUTER_TYPES, label='Computer Type')
    operating_system = CharFilter(lookup_expr='icontains', label='Operating System')
    hostname = CharFilter(lookup_expr='icontains', label='Hostname')
    domain_joined = django_filters.BooleanFilter(label='Domain Joined')
    memory_min = NumberFilter(field_name='memory_gb', lookup_expr='gte', label='Min Memory (GB)')
    memory_max = NumberFilter(field_name='memory_gb', lookup_expr='lte', label='Max Memory (GB)')
    storage_min = NumberFilter(field_name='storage_gb', lookup_expr='gte', label='Min Storage (GB)')
    storage_max = NumberFilter(field_name='storage_gb', lookup_expr='lte', label='Max Storage (GB)')

    class Meta(DeviceFilter.Meta):
        model = Computer
        fields = DeviceFilter.Meta.fields | {
            'computer_type': ['exact'],
            'operating_system': ['exact', 'icontains'],
            'hostname': ['exact', 'icontains'],
            'domain_joined': ['exact'],
            'memory_gb': ['exact', 'gte', 'lte'],
            'storage_gb': ['exact', 'gte', 'lte'],
        }


class PeripheralFilter(DeviceFilter):
    """Filter for peripherals"""
    peripheral_type = ChoiceFilter(choices=Peripheral.PERIPHERAL_TYPES, label='Peripheral Type')
    connected_to = django_filters.ModelChoiceFilter(queryset=Computer.objects.all(), label='Connected To')

    class Meta(DeviceFilter.Meta):
        model = Peripheral
        fields = DeviceFilter.Meta.fields | {
            'peripheral_type': ['exact'],
            'connected_to': ['exact'],
        }
