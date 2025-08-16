from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib import messages
from django.db.models import Count, Q, Sum
from django.utils import timezone
from django.http import JsonResponse
from django.template.loader import render_to_string
from django_tables2 import RequestConfig
from django_filters.views import FilterView
from django_tables2.views import SingleTableMixin
import time
import logging
from .models import (
    Device, Category, Location, Vendor, Software, MaintenanceRecord,
    NetworkDevice, Computer, Peripheral, InventoryAudit
)
from .tables import DeviceTable, SoftwareTable, MaintenanceTable
from .filters import DeviceFilter, SoftwareFilter, MaintenanceFilter
from .forms import DeviceForm, SoftwareForm, MaintenanceForm
from .logging_utils import (
    log_view_access, log_user_action, log_error, log_database_operation,
    log_export_operation, log_maintenance_event, log_software_installation
)

# Get logger for views
logger = logging.getLogger('inventory.views')


@login_required
def dashboard(request):
    """Main dashboard view with overview statistics"""
    start_time = time.time()
    
    try:
        logger.info(f"Dashboard accessed by user: {request.user.username}")
        
        # Get current date for calculations
        today = timezone.now().date()
        
        # Device statistics
        total_devices = Device.objects.count()
        active_devices = Device.objects.filter(status='active').count()
        devices_needing_maintenance = Device.objects.filter(
            next_maintenance__lte=timezone.now()
        ).count()
        devices_under_warranty = Device.objects.filter(
            warranty_expiry__gt=today
        ).count()
        
        # Software statistics
        total_software = Software.objects.count()
        expiring_licenses = Software.objects.filter(
            license_expiry__lte=today + timezone.timedelta(days=30),
            license_expiry__gt=today
        ).count()
        expired_licenses = Software.objects.filter(license_expiry__lt=today).count()
        
        # Maintenance statistics
        pending_maintenance = MaintenanceRecord.objects.filter(
            performed_date__isnull=True,
            scheduled_date__lte=timezone.now()
        ).count()
        
        # Recent activities
        recent_devices = Device.objects.order_by('-created_at')[:5]
        recent_maintenance = MaintenanceRecord.objects.order_by('-created_at')[:5]
        
        # Device status breakdown
        status_breakdown = Device.objects.values('status').annotate(
            count=Count('id')
        ).order_by('status')
        
        # Category breakdown
        category_breakdown = Category.objects.annotate(
            device_count=Count('devices')
        ).order_by('-device_count')[:10]
        
        context = {
            'total_devices': total_devices,
            'active_devices': active_devices,
            'devices_needing_maintenance': devices_needing_maintenance,
            'devices_under_warranty': devices_under_warranty,
            'total_software': total_software,
            'expiring_licenses': expiring_licenses,
            'expired_licenses': expired_licenses,
        'pending_maintenance': pending_maintenance,
            'recent_devices': recent_devices,
            'recent_maintenance': recent_maintenance,
            'status_breakdown': status_breakdown,
            'category_breakdown': category_breakdown,
        }
        
        response_time = time.time() - start_time
        log_view_access('dashboard', request, response_time)
        log_user_action(request.user, 'dashboard_access', f"Response time: {response_time:.3f}s")
        
        logger.info(f"Dashboard rendered successfully in {response_time:.3f}s")
        return render(request, 'inventory/dashboard.html', context)
        
    except Exception as e:
        response_time = time.time() - start_time
        log_error(e, 'dashboard view', request.user, request)
        logger.error(f"Dashboard error after {response_time:.3f}s: {str(e)}")
        messages.error(request, 'An error occurred while loading the dashboard.')
        return render(request, 'inventory/dashboard.html', {})


class DeviceListView(LoginRequiredMixin, SingleTableMixin, FilterView):
    """List view for devices with filtering and sorting"""
    model = Device
    table_class = DeviceTable
    filterset_class = DeviceFilter
    template_name = 'inventory/device_list.html'
    paginate_by = 25

    def get_queryset(self):
        try:
            queryset = super().get_queryset()
            # Add related fields for better performance
            queryset = queryset.select_related('category', 'vendor', 'location', 'assigned_to')
            logger.debug(f"Device list queryset created with {queryset.count()} devices")
            return queryset
        except Exception as e:
            log_error(e, 'DeviceListView.get_queryset', self.request.user, self.request)
            logger.error(f"Error in device list queryset: {str(e)}")
            return Device.objects.none()

    def get_context_data(self, **kwargs):
        try:
            context = super().get_context_data(**kwargs)
            queryset = self.get_queryset()
            context['total_devices'] = queryset.count()
            context['active_devices'] = queryset.filter(status='active').count()
            
            logger.info(f"Device list context created - Total: {context['total_devices']}, Active: {context['active_devices']}")
            return context
        except Exception as e:
            log_error(e, 'DeviceListView.get_context_data', self.request.user, self.request)
            logger.error(f"Error in device list context: {str(e)}")
            return super().get_context_data(**kwargs)

    def dispatch(self, request, *args, **kwargs):
        try:
            start_time = time.time()
            response = super().dispatch(request, *args, **kwargs)
            response_time = time.time() - start_time
            
            log_view_access('device_list', request, response_time)
            log_user_action(request.user, 'device_list_access', f"Response time: {response_time:.3f}s")
            
            logger.info(f"Device list accessed successfully in {response_time:.3f}s")
            return response
        except Exception as e:
            response_time = time.time() - start_time if 'start_time' in locals() else 0
            log_error(e, 'DeviceListView.dispatch', request.user, request)
            logger.error(f"Device list error after {response_time:.3f}s: {str(e)}")
            messages.error(request, 'An error occurred while loading the device list.')
            raise


class DeviceDetailView(LoginRequiredMixin, DetailView):
    """Detail view for a single device"""
    model = Device
    template_name = 'inventory/device_detail.html'
    context_object_name = 'device'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        device = self.get_object()
        
        # Get related data
        context['software_installations'] = device.software_installations.select_related('software')
        context['maintenance_records'] = device.maintenance_records.order_by('-performed_date', '-scheduled_date')
        
        return context


class DeviceCreateView(LoginRequiredMixin, CreateView):
    """Create view for new devices"""
    model = Device
    form_class = DeviceForm
    template_name = 'inventory/device_form.html'
    success_url = reverse_lazy('device_list')

    def form_valid(self, form):
        try:
            response = super().form_valid(form)
            
            # Log the successful device creation
            device = form.instance
            log_database_operation(
                operation="CREATE",
                model="Device",
                record_id=device.id,
                user=self.request.user,
                details=f"Device '{device.asset_tag}' created"
            )
            log_user_action(
                self.request.user,
                'device_created',
                f"Device ID: {device.id}, Asset Tag: {device.asset_tag}"
            )
            
            logger.info(f"Device created successfully - ID: {device.id}, Asset Tag: {device.asset_tag}")
            messages.success(self.request, 'Device created successfully!')
            return response
            
        except Exception as e:
            log_error(e, 'DeviceCreateView.form_valid', self.request.user, self.request)
            logger.error(f"Error creating device: {str(e)}")
            messages.error(self.request, 'An error occurred while creating the device.')
            return self.form_invalid(form)

    def form_invalid(self, form):
        try:
            logger.warning(f"Device creation form invalid - Errors: {form.errors}")
            log_user_action(
                self.request.user,
                'device_creation_failed',
                f"Form errors: {form.errors}"
            )
            return super().form_invalid(form)
        except Exception as e:
            log_error(e, 'DeviceCreateView.form_invalid', self.request.user, self.request)
            return super().form_invalid(form)


class DeviceUpdateView(LoginRequiredMixin, UpdateView):
    """Update view for existing devices"""
    model = Device
    form_class = DeviceForm
    template_name = 'inventory/device_form.html'

    def get_success_url(self):
        return reverse_lazy('device_detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        messages.success(self.request, 'Device updated successfully!')
        return super().form_valid(form)


class DeviceDeleteView(LoginRequiredMixin, DeleteView):
    """Delete view for devices"""
    model = Device
    template_name = 'inventory/device_confirm_delete.html'
    success_url = reverse_lazy('device_list')

    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Device deleted successfully!')
        return super().delete(request, *args, **kwargs)


class SoftwareListView(LoginRequiredMixin, SingleTableMixin, FilterView):
    """List view for software with filtering and sorting"""
    model = Software
    table_class = SoftwareTable
    filterset_class = SoftwareFilter
    template_name = 'inventory/software_list.html'
    paginate_by = 25

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_software'] = self.get_queryset().count()
        context['expiring_licenses'] = self.get_queryset().filter(
            license_expiry__lte=timezone.now().date() + timezone.timedelta(days=30),
            license_expiry__gt=timezone.now().date()
        ).count()
        return context


class SoftwareDetailView(LoginRequiredMixin, DetailView):
    """Detail view for software"""
    model = Software
    template_name = 'inventory/software_detail.html'
    context_object_name = 'software'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        software = self.get_object()
        context['installations'] = software.installations.select_related('device', 'installed_by')
        return context


class SoftwareCreateView(LoginRequiredMixin, CreateView):
    """Create view for new software"""
    model = Software
    form_class = SoftwareForm
    template_name = 'inventory/software_form.html'
    success_url = reverse_lazy('software_list')

    def form_valid(self, form):
        messages.success(self.request, 'Software added successfully!')
        return super().form_valid(form)


class SoftwareUpdateView(LoginRequiredMixin, UpdateView):
    """Update view for software"""
    model = Software
    form_class = SoftwareForm
    template_name = 'inventory/software_form.html'

    def get_success_url(self):
        return reverse_lazy('software_detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        messages.success(self.request, 'Software updated successfully!')
        return super().form_valid(form)


class SoftwareDeleteView(LoginRequiredMixin, DeleteView):
    """Delete view for software"""
    model = Software
    template_name = 'inventory/software_confirm_delete.html'
    success_url = reverse_lazy('software_list')

    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Software deleted successfully!')
        return super().delete(request, *args, **kwargs)


class MaintenanceListView(LoginRequiredMixin, SingleTableMixin, FilterView):
    """List view for maintenance records"""
    model = MaintenanceRecord
    table_class = MaintenanceTable
    filterset_class = MaintenanceFilter
    template_name = 'inventory/maintenance_list.html'
    paginate_by = 25

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['pending_maintenance'] = self.get_queryset().filter(
            performed_date__isnull=True,
            scheduled_date__lte=timezone.now()
        ).count()
        return context


class MaintenanceCreateView(LoginRequiredMixin, CreateView):
    """Create view for maintenance records"""
    model = MaintenanceRecord
    form_class = MaintenanceForm
    template_name = 'inventory/maintenance_form.html'
    success_url = reverse_lazy('maintenance_list')

    def form_valid(self, form):
        form.instance.performed_by = self.request.user
        messages.success(self.request, 'Maintenance record created successfully!')
        return super().form_valid(form)


class MaintenanceUpdateView(LoginRequiredMixin, UpdateView):
    """Update view for maintenance records"""
    model = MaintenanceRecord
    form_class = MaintenanceForm
    template_name = 'inventory/maintenance_form.html'
    success_url = reverse_lazy('maintenance_list')

    def form_valid(self, form):
        messages.success(self.request, 'Maintenance record updated successfully!')
        return super().form_valid(form)


class MaintenanceDeleteView(LoginRequiredMixin, DeleteView):
    """Delete view for maintenance records"""
    model = MaintenanceRecord
    template_name = 'inventory/maintenance_confirm_delete.html'
    success_url = reverse_lazy('maintenance_list')

    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Maintenance record deleted successfully!')
        return super().delete(request, *args, **kwargs)


@login_required
def category_list(request):
    """List view for categories"""
    categories = Category.objects.annotate(device_count=Count('devices')).order_by('name')
    return render(request, 'inventory/category_list.html', {'categories': categories})


@login_required
def location_list(request):
    """List view for locations"""
    locations = Location.objects.annotate(device_count=Count('devices')).order_by('name')
    return render(request, 'inventory/location_list.html', {'locations': locations})


@login_required
def vendor_list(request):
    """List view for vendors"""
    vendors = Vendor.objects.annotate(device_count=Count('devices')).order_by('name')
    return render(request, 'inventory/vendor_list.html', {'vendors': vendors})


@login_required
def search(request):
    """Search functionality across all models"""
    query = request.GET.get('q', '')
    results = {}
    
    if query:
        # Search in devices
        devices = Device.objects.filter(
            Q(asset_tag__icontains=query) |
            Q(serial_number__icontains=query) |
            Q(model__icontains=query) |
            Q(notes__icontains=query)
        )[:10]
        results['devices'] = devices
        
        # Search in software
        software = Software.objects.filter(
            Q(name__icontains=query) |
            Q(version__icontains=query) |
            Q(license_key__icontains=query)
        )[:10]
        results['software'] = software
        
        # Search in locations
        locations = Location.objects.filter(
            Q(name__icontains=query) |
            Q(building__icontains=query) |
            Q(room__icontains=query)
        )[:5]
        results['locations'] = locations
    
    return render(request, 'inventory/search.html', {
        'query': query,
        'results': results
    })


@login_required
def device_quick_actions(request, pk):
    """Quick actions for devices (AJAX)"""
    device = get_object_or_404(Device, pk=pk)
    action = request.POST.get('action')
    
    if action == 'mark_maintenance':
        device.status = 'maintenance'
        device.save()
        return JsonResponse({'status': 'success', 'message': 'Device marked for maintenance'})
    
    elif action == 'mark_active':
        device.status = 'active'
        device.save()
        return JsonResponse({'status': 'success', 'message': 'Device marked as active'})
    
    elif action == 'mark_retired':
        device.status = 'retired'
        device.save()
        return JsonResponse({'status': 'success', 'message': 'Device marked as retired'})
    
    return JsonResponse({'status': 'error', 'message': 'Invalid action'})


@login_required
def export_devices(request):
    """Export devices to CSV"""
    import csv
    from django.http import HttpResponse
    
    try:
        start_time = time.time()
        logger.info(f"Device export started by user: {request.user.username}")
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="devices.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'Asset Tag', 'Model', 'Category', 'Status', 'Condition', 
            'Location', 'Assigned To', 'Serial Number', 'Purchase Date', 
            'Warranty Expiry', 'Purchase Price'
        ])
        
        devices = Device.objects.select_related('category', 'location', 'assigned_to')
        device_count = devices.count()
        
        for device in devices:
            writer.writerow([
                device.asset_tag,
                device.model,
                device.category.name if device.category else '',
                device.get_status_display(),
                device.get_condition_display(),
                str(device.location) if device.location else '',
                device.assigned_to.get_full_name() if device.assigned_to else '',
                device.serial_number,
                device.purchase_date,
                device.warranty_expiry,
                device.purchase_price,
            ])
        
        response_time = time.time() - start_time
        
        # Log the export operation
        log_export_operation('devices', request.user, device_count, 'csv')
        log_user_action(
            request.user,
            'devices_exported',
            f"Exported {device_count} devices in {response_time:.3f}s"
        )
        
        logger.info(f"Device export completed successfully - {device_count} devices exported in {response_time:.3f}s")
        return response
        
    except Exception as e:
        response_time = time.time() - start_time if 'start_time' in locals() else 0
        log_error(e, 'export_devices', request.user, request)
        logger.error(f"Device export failed after {response_time:.3f}s: {str(e)}")
        messages.error(request, 'An error occurred while exporting devices.')
        return HttpResponse('Export failed', status=500)


@login_required
def logout_view(request):
    """Custom logout view"""
    try:
        logger.info(f"User logout: {request.user.username}")
        log_user_action(request.user, 'logout', 'User logged out successfully')
        
        from django.contrib.auth import logout
        logout(request)
        
        messages.success(request, 'You have been successfully logged out.')
        return redirect('inventory:dashboard')
        
    except Exception as e:
        log_error(e, 'logout_view', request.user, request)
        logger.error(f"Logout error: {str(e)}")
        messages.error(request, 'An error occurred during logout.')
        return redirect('inventory:dashboard')
