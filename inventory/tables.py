import django_tables2 as tables
from django_tables2 import A, Column
from django.utils.html import format_html
from django.urls import reverse
from .models import Device, Software, MaintenanceRecord
from django.utils import timezone


class DeviceTable(tables.Table):
    """Table for displaying devices"""
    asset_tag = tables.LinkColumn('device_detail', args=[A('pk')])
    category = tables.Column()
    status = tables.Column()
    condition = tables.Column()
    location = tables.Column()
    assigned_to = tables.Column()
    warranty_status = tables.Column(empty_values=(), orderable=False)
    maintenance_status = tables.Column(empty_values=(), orderable=False)
    actions = tables.Column(empty_values=(), orderable=False)

    class Meta:
        model = Device
        template_name = "django_tables2/bootstrap5.html"
        fields = (
            'asset_tag', 'model', 'category', 'status', 'condition',
            'location', 'assigned_to', 'warranty_status', 'maintenance_status', 'actions'
        )
        attrs = {
            'class': 'table table-striped table-hover',
            'thead': {'class': 'table-dark'},
        }

    def render_status(self, value):
        status_colors = {
            'active': 'success',
            'inactive': 'secondary',
            'maintenance': 'warning',
            'retired': 'danger',
            'lost': 'dark',
        }
        color = status_colors.get(value, 'secondary')
        return format_html('<span class="badge bg-{}">{}</span>', color, value.title())

    def render_condition(self, value):
        condition_colors = {
            'excellent': 'success',
            'good': 'info',
            'fair': 'warning',
            'poor': 'danger',
            'broken': 'dark',
        }
        color = condition_colors.get(value, 'secondary')
        return format_html('<span class="badge bg-{}">{}</span>', color, value.title())

    def render_warranty_status(self, record):
        if record.is_under_warranty():
            return format_html('<span class="text-success">✓ Under Warranty</span>')
        elif record.warranty_expiry:
            return format_html('<span class="text-danger">✗ Expired</span>')
        return format_html('<span class="text-muted">- No Warranty</span>')

    def render_maintenance_status(self, record):
        if record.needs_maintenance():
            return format_html('<span class="text-warning">⚠ Needs Maintenance</span>')
        return format_html('<span class="text-success">✓ OK</span>')

    def render_actions(self, record):
        edit_url = reverse('device_update', args=[record.pk])
        delete_url = reverse('device_delete', args=[record.pk])
        
        return format_html(
            '<div class="btn-group btn-group-sm" role="group">'
            '<a href="{}" class="btn btn-outline-primary">Edit</a>'
            '<a href="{}" class="btn btn-outline-danger">Delete</a>'
            '</div>',
            edit_url, delete_url
        )


class SoftwareTable(tables.Table):
    """Table for displaying software"""
    name = tables.LinkColumn('software_detail', args=[A('pk')])
    vendor = tables.Column()
    license_type = tables.Column()
    license_status = tables.Column(empty_values=(), orderable=False)
    available_seats = tables.Column(empty_values=(), orderable=False)
    actions = tables.Column(empty_values=(), orderable=False)

    class Meta:
        model = Software
        template_name = "django_tables2/bootstrap5.html"
        fields = (
            'name', 'version', 'vendor', 'license_type', 'seats', 'used_seats',
            'available_seats', 'license_status', 'actions'
        )
        attrs = {
            'class': 'table table-striped table-hover',
            'thead': {'class': 'table-dark'},
        }

    def render_license_type(self, value):
        type_colors = {
            'perpetual': 'success',
            'subscription': 'info',
            'trial': 'warning',
            'open_source': 'secondary',
        }
        color = type_colors.get(value, 'secondary')
        return format_html('<span class="badge bg-{}">{}</span>', color, value.title())

    def render_license_status(self, record):
        if record.is_expired():
            return format_html('<span class="text-danger">✗ Expired</span>')
        elif record.license_expiry:
            return format_html('<span class="text-success">✓ Active</span>')
        return format_html('<span class="text-muted">- No Expiry</span>')

    def render_available_seats(self, record):
        available = record.available_seats()
        if available <= 0:
            return format_html('<span class="text-danger">{} (Full)</span>', available)
        elif available <= 2:
            return format_html('<span class="text-warning">{}</span>', available)
        return format_html('<span class="text-success">{}</span>', available)

    def render_actions(self, record):
        edit_url = reverse('software_update', args=[record.pk])
        delete_url = reverse('software_delete', args=[record.pk])
        
        return format_html(
            '<div class="btn-group btn-group-sm" role="group">'
            '<a href="{}" class="btn btn-outline-primary">Edit</a>'
            '<a href="{}" class="btn btn-outline-danger">Delete</a>'
            '</div>',
            edit_url, delete_url
        )


class MaintenanceTable(tables.Table):
    """Table for displaying maintenance records"""
    device = tables.LinkColumn('device_detail', args=[A('device.pk')])
    maintenance_type = tables.Column()
    status = tables.Column(empty_values=(), orderable=False)
    cost = tables.Column()
    actions = tables.Column(empty_values=(), orderable=False)

    class Meta:
        model = MaintenanceRecord
        template_name = "django_tables2/bootstrap5.html"
        fields = (
            'device', 'maintenance_type', 'performed_by', 'scheduled_date',
            'performed_date', 'status', 'cost', 'actions'
        )
        attrs = {
            'class': 'table table-striped table-hover',
            'thead': {'class': 'table-dark'},
        }

    def render_maintenance_type(self, value):
        type_colors = {
            'preventive': 'success',
            'corrective': 'danger',
            'upgrade': 'info',
            'inspection': 'warning',
        }
        color = type_colors.get(value, 'secondary')
        return format_html('<span class="badge bg-{}">{}</span>', color, value.title())

    def render_status(self, record):
        if record.performed_date:
            return format_html('<span class="text-success">✓ Completed</span>')
        elif record.scheduled_date and record.scheduled_date < timezone.now():
            return format_html('<span class="text-danger">⚠ Overdue</span>')
        elif record.scheduled_date:
            return format_html('<span class="text-info">📅 Scheduled</span>')
        return format_html('<span class="text-muted">- Pending</span>')

    def render_cost(self, value):
        if value:
            return format_html('${:.2f}', value)
        return '-'

    def render_actions(self, record):
        edit_url = reverse('maintenance_update', args=[record.pk])
        delete_url = reverse('maintenance_delete', args=[record.pk])
        
        return format_html(
            '<div class="btn-group btn-group-sm" role="group">'
            '<a href="{}" class="btn btn-outline-primary">Edit</a>'
            '<a href="{}" class="btn btn-outline-danger">Delete</a>'
            '</div>',
            edit_url, delete_url
        )


class NetworkDeviceTable(DeviceTable):
    """Table for displaying network devices"""
    ip_address = tables.Column()
    hostname = tables.Column()
    is_managed = tables.BooleanColumn()

    class Meta(DeviceTable.Meta):
        fields = DeviceTable.Meta.fields + ('ip_address', 'hostname', 'is_managed')

    def render_is_managed(self, value):
        if value:
            return format_html('<span class="text-success">✓ Managed</span>')
        return format_html('<span class="text-muted">- Unmanaged</span>')


class ComputerTable(DeviceTable):
    """Table for displaying computers"""
    computer_type = tables.Column()
    operating_system = tables.Column()
    hostname = tables.Column()

    class Meta(DeviceTable.Meta):
        fields = DeviceTable.Meta.fields + ('computer_type', 'operating_system', 'hostname')

    def render_computer_type(self, value):
        type_colors = {
            'desktop': 'primary',
            'laptop': 'info',
            'server': 'danger',
            'workstation': 'warning',
            'thin_client': 'secondary',
        }
        color = type_colors.get(value, 'secondary')
        return format_html('<span class="badge bg-{}">{}</span>', color, value.title())


class PeripheralTable(DeviceTable):
    """Table for displaying peripherals"""
    peripheral_type = tables.Column()
    connected_to = tables.LinkColumn('device_detail', args=[A('connected_to.pk')])

    class Meta(DeviceTable.Meta):
        fields = DeviceTable.Meta.fields + ('peripheral_type', 'connected_to')

    def render_peripheral_type(self, value):
        type_colors = {
            'monitor': 'primary',
            'keyboard': 'secondary',
            'mouse': 'info',
            'printer': 'warning',
            'scanner': 'success',
            'speaker': 'danger',
            'headset': 'dark',
            'webcam': 'light',
            'other': 'muted',
        }
        color = type_colors.get(value, 'secondary')
        return format_html('<span class="badge bg-{}">{}</span>', color, value.title())
