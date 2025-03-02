from django.contrib import admin
from .models import InventoryTransaction, LowStockAlert, PriceChangeLog

@admin.register(InventoryTransaction)
class InventoryTransactionAdmin(admin.ModelAdmin):
    list_display = ('product', 'transaction_type', 'quantity', 'previous_stock', 'new_stock', 'performed_by', 'timestamp')
    list_filter = ('transaction_type', 'timestamp', 'performed_by')
    search_fields = ('product__name', 'notes', 'performed_by__username')
    readonly_fields = ('product', 'quantity', 'previous_stock', 'new_stock', 'transaction_type', 'performed_by', 'timestamp')
    date_hierarchy = 'timestamp'

@admin.register(LowStockAlert)
class LowStockAlertAdmin(admin.ModelAdmin):
    list_display = ('product', 'stock_level', 'threshold', 'status', 'created_at', 'acknowledged_by')
    list_filter = ('status', 'created_at', 'threshold')
    search_fields = ('product__name', 'acknowledged_by__username')
    readonly_fields = ('product', 'stock_level', 'threshold', 'created_at')
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Alert Information', {
            'fields': ('product', 'stock_level', 'threshold', 'status', 'created_at')
        }),
        ('Resolution Information', {
            'fields': ('acknowledged_by', 'acknowledged_at', 'resolved_at')
        }),
    )

@admin.register(PriceChangeLog)
class PriceChangeLogAdmin(admin.ModelAdmin):
    list_display = ('product', 'old_price', 'new_price', 'changed_by', 'changed_at')
    list_filter = ('changed_at', 'changed_by')
    search_fields = ('product__name', 'notes', 'changed_by__username')
    readonly_fields = ('product', 'old_price', 'new_price', 'changed_by', 'changed_at')
    date_hierarchy = 'changed_at'
