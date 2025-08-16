from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import api_views

app_name = 'api'

# Create a router and register our viewsets with it
router = DefaultRouter()
router.register(r'devices', api_views.DeviceViewSet, basename='device')
router.register(r'network-devices', api_views.NetworkDeviceViewSet, basename='networkdevice')
router.register(r'computers', api_views.ComputerViewSet, basename='computer')
router.register(r'peripherals', api_views.PeripheralViewSet, basename='peripheral')
router.register(r'software', api_views.SoftwareViewSet, basename='software')
router.register(r'maintenance', api_views.MaintenanceRecordViewSet, basename='maintenance')
router.register(r'categories', api_views.CategoryViewSet, basename='category')
router.register(r'locations', api_views.LocationViewSet, basename='location')
router.register(r'vendors', api_views.VendorViewSet, basename='vendor')

urlpatterns = [
    # Include the router URLs
    path('', include(router.urls)),
    
    # Dashboard API endpoints
    path('dashboard/stats/', api_views.dashboard_stats, name='dashboard-stats'),
    path('dashboard/recent/', api_views.recent_activity, name='recent-activity'),
]
