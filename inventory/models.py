from django.db import models
from django.utils import timezone
from core.models import Product, CustomUser

class InventoryTransaction(models.Model):
    TRANSACTION_TYPES = (
        ('add', 'Stock Added'),
        ('remove', 'Stock Removed'),
        ('adjust', 'Stock Adjusted'),
        ('initial', 'Initial Stock'),
    )
    
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='inventory_transactions')
    quantity = models.IntegerField(help_text="Positive for additions, negative for removals")
    previous_stock = models.PositiveIntegerField()
    new_stock = models.PositiveIntegerField()
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)
    notes = models.TextField(blank=True, null=True)
    performed_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, related_name='inventory_transactions')
    timestamp = models.DateTimeField(default=timezone.now)
    
    def __str__(self):
        return f"{self.transaction_type} - {self.product.name} ({self.quantity})"
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['product', 'timestamp']),
            models.Index(fields=['transaction_type']),
            models.Index(fields=['performed_by']),
        ]

class LowStockAlert(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('acknowledged', 'Acknowledged'),
        ('resolved', 'Resolved'),
    )
    
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='low_stock_alerts')
    stock_level = models.PositiveIntegerField()
    threshold = models.PositiveIntegerField()
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(default=timezone.now)
    acknowledged_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='acknowledged_alerts')
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"Low Stock Alert - {self.product.name} ({self.stock_level})"
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['product', 'status']),
            models.Index(fields=['status']),
            models.Index(fields=['created_at']),
        ]

class PriceChangeLog(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='price_changes')
    old_price = models.PositiveBigIntegerField()
    new_price = models.PositiveBigIntegerField()
    changed_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, related_name='price_changes')
    changed_at = models.DateTimeField(default=timezone.now)
    notes = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return f"Price Change - {self.product.name} ({self.old_price} → {self.new_price})"
    
    class Meta:
        ordering = ['-changed_at']
        indexes = [
            models.Index(fields=['product', 'changed_at']),
            models.Index(fields=['changed_by']),
        ]
