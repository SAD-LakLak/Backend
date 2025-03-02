from rest_framework import serializers
from core.models import Product
from .models import InventoryTransaction, LowStockAlert, PriceChangeLog

class ProductInventorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['id', 'name', 'stock', 'price', 'type', 'provider', 'is_active']

class InventoryTransactionSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    performed_by_name = serializers.CharField(source='performed_by.username', read_only=True)
    
    class Meta:
        model = InventoryTransaction
        fields = ['id', 'product', 'product_name', 'quantity', 'previous_stock', 'new_stock', 
                  'transaction_type', 'notes', 'performed_by', 'performed_by_name', 'timestamp']
        read_only_fields = ['id', 'previous_stock', 'new_stock', 'timestamp', 'product_name', 'performed_by_name']

class LowStockAlertSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    acknowledged_by_name = serializers.CharField(source='acknowledged_by.username', read_only=True, allow_null=True)
    
    class Meta:
        model = LowStockAlert
        fields = ['id', 'product', 'product_name', 'stock_level', 'threshold', 'status',
                  'created_at', 'acknowledged_by', 'acknowledged_by_name', 'acknowledged_at', 'resolved_at']
        read_only_fields = ['id', 'product', 'product_name', 'stock_level', 'threshold', 
                           'created_at', 'acknowledged_by_name']

class PriceChangeLogSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    changed_by_name = serializers.CharField(source='changed_by.username', read_only=True, allow_null=True)
    
    class Meta:
        model = PriceChangeLog
        fields = ['id', 'product', 'product_name', 'old_price', 'new_price', 
                  'changed_by', 'changed_by_name', 'changed_at', 'notes']
        read_only_fields = ['id', 'product', 'product_name', 'old_price', 'new_price', 
                           'changed_by', 'changed_by_name', 'changed_at']

class StockUpdateSerializer(serializers.Serializer):
    product_id = serializers.IntegerField()
    quantity = serializers.IntegerField()
    notes = serializers.CharField(required=False, allow_blank=True)
    transaction_type = serializers.ChoiceField(choices=InventoryTransaction.TRANSACTION_TYPES)

class BulkStockUpdateSerializer(serializers.Serializer):
    product_ids = serializers.ListField(child=serializers.IntegerField())
    quantity = serializers.IntegerField()
    notes = serializers.CharField(required=False, allow_blank=True)
    transaction_type = serializers.ChoiceField(choices=InventoryTransaction.TRANSACTION_TYPES)

class PriceUpdateSerializer(serializers.Serializer):
    product_id = serializers.IntegerField()
    new_price = serializers.IntegerField(min_value=0)
    notes = serializers.CharField(required=False, allow_blank=True)

class BulkPriceUpdateSerializer(serializers.Serializer):
    product_ids = serializers.ListField(child=serializers.IntegerField())
    new_price = serializers.IntegerField(min_value=0)
    notes = serializers.CharField(required=False, allow_blank=True) 