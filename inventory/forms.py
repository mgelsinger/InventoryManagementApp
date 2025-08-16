from django import forms
from django.contrib.auth.models import User
from .models import (
    Device, Category, Location, Vendor, Software, MaintenanceRecord,
    NetworkDevice, Computer, Peripheral
)


class DeviceForm(forms.ModelForm):
    """Form for creating and editing devices"""
    
    class Meta:
        model = Device
        fields = [
            'asset_tag', 'serial_number', 'model', 'category', 'vendor',
            'status', 'condition', 'location', 'assigned_to', 'specifications',
            'purchase_date', 'warranty_expiry', 'purchase_price', 'notes', 'image'
        ]
        widgets = {
            'asset_tag': forms.TextInput(attrs={'class': 'form-control'}),
            'serial_number': forms.TextInput(attrs={'class': 'form-control'}),
            'model': forms.TextInput(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'vendor': forms.Select(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'condition': forms.Select(attrs={'class': 'form-control'}),
            'location': forms.Select(attrs={'class': 'form-control'}),
            'assigned_to': forms.Select(attrs={'class': 'form-control'}),
            'specifications': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'purchase_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'warranty_expiry': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'purchase_price': forms.NumberInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
        }

    def clean_asset_tag(self):
        asset_tag = self.cleaned_data['asset_tag']
        if not asset_tag:
            raise forms.ValidationError("Asset tag is required.")
        
        # Check for uniqueness
        if self.instance.pk:
            # Exclude current instance for updates
            if Device.objects.filter(asset_tag=asset_tag).exclude(pk=self.instance.pk).exists():
                raise forms.ValidationError("This asset tag is already in use.")
        else:
            # Check for new instances
            if Device.objects.filter(asset_tag=asset_tag).exists():
                raise forms.ValidationError("This asset tag is already in use.")
        
        return asset_tag

    def clean(self):
        cleaned_data = super().clean()
        purchase_date = cleaned_data.get('purchase_date')
        warranty_expiry = cleaned_data.get('warranty_expiry')
        
        if purchase_date and warranty_expiry and warranty_expiry < purchase_date:
            raise forms.ValidationError("Warranty expiry date cannot be before purchase date.")
        
        return cleaned_data


class NetworkDeviceForm(DeviceForm):
    """Form for network devices"""
    
    class Meta(DeviceForm.Meta):
        model = NetworkDevice
        fields = DeviceForm.Meta.fields + [
            'ip_address', 'mac_address', 'hostname', 'network_segment',
            'is_managed', 'management_ip'
        ]
        widgets = {
            **DeviceForm.Meta.widgets,
            'ip_address': forms.TextInput(attrs={'class': 'form-control'}),
            'mac_address': forms.TextInput(attrs={'class': 'form-control'}),
            'hostname': forms.TextInput(attrs={'class': 'form-control'}),
            'network_segment': forms.TextInput(attrs={'class': 'form-control'}),
            'is_managed': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'management_ip': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def clean_mac_address(self):
        mac_address = self.cleaned_data['mac_address']
        if mac_address:
            # Basic MAC address validation
            import re
            mac_pattern = re.compile(r'^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$')
            if not mac_pattern.match(mac_address):
                raise forms.ValidationError("Please enter a valid MAC address (e.g., 00:11:22:33:44:55)")
        return mac_address


class ComputerForm(DeviceForm):
    """Form for computers"""
    
    class Meta(DeviceForm.Meta):
        model = Computer
        fields = DeviceForm.Meta.fields + [
            'computer_type', 'operating_system', 'os_version', 'processor',
            'memory_gb', 'storage_gb', 'hostname', 'ip_address', 'mac_address',
            'domain_joined', 'domain_name'
        ]
        widgets = {
            **DeviceForm.Meta.widgets,
            'computer_type': forms.Select(attrs={'class': 'form-control'}),
            'operating_system': forms.TextInput(attrs={'class': 'form-control'}),
            'os_version': forms.TextInput(attrs={'class': 'form-control'}),
            'processor': forms.TextInput(attrs={'class': 'form-control'}),
            'memory_gb': forms.NumberInput(attrs={'class': 'form-control'}),
            'storage_gb': forms.NumberInput(attrs={'class': 'form-control'}),
            'hostname': forms.TextInput(attrs={'class': 'form-control'}),
            'ip_address': forms.TextInput(attrs={'class': 'form-control'}),
            'mac_address': forms.TextInput(attrs={'class': 'form-control'}),
            'domain_joined': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'domain_name': forms.TextInput(attrs={'class': 'form-control'}),
        }


class PeripheralForm(DeviceForm):
    """Form for peripherals"""
    
    class Meta(DeviceForm.Meta):
        model = Peripheral
        fields = DeviceForm.Meta.fields + ['peripheral_type', 'connected_to']
        widgets = {
            **DeviceForm.Meta.widgets,
            'peripheral_type': forms.Select(attrs={'class': 'form-control'}),
            'connected_to': forms.Select(attrs={'class': 'form-control'}),
        }


class SoftwareForm(forms.ModelForm):
    """Form for software"""
    
    class Meta:
        model = Software
        fields = [
            'name', 'version', 'vendor', 'license_type', 'license_key',
            'license_expiry', 'seats', 'purchase_date', 'purchase_price', 'notes'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'version': forms.TextInput(attrs={'class': 'form-control'}),
            'vendor': forms.Select(attrs={'class': 'form-control'}),
            'license_type': forms.Select(attrs={'class': 'form-control'}),
            'license_key': forms.TextInput(attrs={'class': 'form-control'}),
            'license_expiry': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'seats': forms.NumberInput(attrs={'class': 'form-control'}),
            'purchase_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'purchase_price': forms.NumberInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def clean_seats(self):
        seats = self.cleaned_data['seats']
        if seats < 1:
            raise forms.ValidationError("Number of seats must be at least 1.")
        return seats

    def clean(self):
        cleaned_data = super().clean()
        purchase_date = cleaned_data.get('purchase_date')
        license_expiry = cleaned_data.get('license_expiry')
        
        if purchase_date and license_expiry and license_expiry < purchase_date:
            raise forms.ValidationError("License expiry date cannot be before purchase date.")
        
        return cleaned_data


class MaintenanceForm(forms.ModelForm):
    """Form for maintenance records"""
    
    class Meta:
        model = MaintenanceRecord
        fields = [
            'device', 'maintenance_type', 'description', 'vendor',
            'scheduled_date', 'performed_date', 'cost', 'parts_used', 'notes'
        ]
        widgets = {
            'device': forms.Select(attrs={'class': 'form-control'}),
            'maintenance_type': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'vendor': forms.Select(attrs={'class': 'form-control'}),
            'scheduled_date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'performed_date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'cost': forms.NumberInput(attrs={'class': 'form-control'}),
            'parts_used': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def clean(self):
        cleaned_data = super().clean()
        scheduled_date = cleaned_data.get('scheduled_date')
        performed_date = cleaned_data.get('performed_date')
        
        if scheduled_date and performed_date and performed_date < scheduled_date:
            raise forms.ValidationError("Performed date cannot be before scheduled date.")
        
        return cleaned_data


class CategoryForm(forms.ModelForm):
    """Form for categories"""
    
    class Meta:
        model = Category
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class LocationForm(forms.ModelForm):
    """Form for locations"""
    
    class Meta:
        model = Location
        fields = ['name', 'building', 'floor', 'room', 'address', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'building': forms.TextInput(attrs={'class': 'form-control'}),
            'floor': forms.TextInput(attrs={'class': 'form-control'}),
            'room': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class VendorForm(forms.ModelForm):
    """Form for vendors"""
    
    class Meta:
        model = Vendor
        fields = ['name', 'contact_person', 'email', 'phone', 'website', 'address']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'contact_person': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'website': forms.URLInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def clean_email(self):
        email = self.cleaned_data['email']
        if email:
            # Basic email validation
            import re
            email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
            if not email_pattern.match(email):
                raise forms.ValidationError("Please enter a valid email address.")
        return email


class SearchForm(forms.Form):
    """Form for search functionality"""
    query = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search devices, software, locations...'
        })
    )
    category = forms.ModelChoiceField(
        queryset=Category.objects.all(),
        required=False,
        empty_label="All Categories",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    status = forms.ChoiceField(
        choices=[('', 'All Statuses')] + Device.STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
