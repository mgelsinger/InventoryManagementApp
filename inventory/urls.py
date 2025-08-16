from django.urls import path
from . import views

app_name = 'inventory'

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),
    
    # Device URLs
    path('devices/', views.DeviceListView.as_view(), name='device_list'),
    path('devices/create/', views.DeviceCreateView.as_view(), name='device_create'),
    path('devices/<int:pk>/', views.DeviceDetailView.as_view(), name='device_detail'),
    path('devices/<int:pk>/edit/', views.DeviceUpdateView.as_view(), name='device_update'),
    path('devices/<int:pk>/delete/', views.DeviceDeleteView.as_view(), name='device_delete'),
    path('devices/<int:pk>/quick-actions/', views.device_quick_actions, name='device_quick_actions'),
    
    # Software URLs
    path('software/', views.SoftwareListView.as_view(), name='software_list'),
    path('software/create/', views.SoftwareCreateView.as_view(), name='software_create'),
    path('software/<int:pk>/', views.SoftwareDetailView.as_view(), name='software_detail'),
    path('software/<int:pk>/edit/', views.SoftwareUpdateView.as_view(), name='software_update'),
    path('software/<int:pk>/delete/', views.SoftwareDeleteView.as_view(), name='software_delete'),
    
    # Maintenance URLs
    path('maintenance/', views.MaintenanceListView.as_view(), name='maintenance_list'),
    path('maintenance/create/', views.MaintenanceCreateView.as_view(), name='maintenance_create'),
    path('maintenance/<int:pk>/edit/', views.MaintenanceUpdateView.as_view(), name='maintenance_update'),
    path('maintenance/<int:pk>/delete/', views.MaintenanceDeleteView.as_view(), name='maintenance_delete'),
    
    # Category, Location, Vendor URLs
    path('categories/', views.category_list, name='category_list'),
    path('locations/', views.location_list, name='location_list'),
    path('vendors/', views.vendor_list, name='vendor_list'),
    
    # Search and Export
    path('search/', views.search, name='search'),
    path('export/devices/', views.export_devices, name='export_devices'),
    
    # Authentication
    path('logout/', views.logout_view, name='logout'),
]
