from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'products', views.ProductInventoryViewSet, basename='inventory-products')
router.register(r'transactions', views.InventoryTransactionViewSet, basename='inventory-transactions')
router.register(r'alerts', views.LowStockAlertViewSet, basename='low-stock-alerts')
router.register(r'price-history', views.PriceChangeLogViewSet, basename='price-history')

urlpatterns = [
    path('', include(router.urls)),
    path('update-stock/', views.update_stock, name='update-stock'),
    path('bulk-update-stock/', views.bulk_update_stock, name='bulk-update-stock'),
    path('update-price/', views.update_price, name='update-price'),
    path('bulk-update-price/', views.bulk_update_price, name='bulk-update-price'),
    path('dashboard/', views.InventoryDashboardView.as_view(), name='inventory-dashboard'),
    path('export/', views.export_inventory, name='export-inventory'),
    path('import/', views.import_inventory, name='import-inventory'),
    path('reports/', views.generate_inventory_report, name='inventory-reports'),
] 