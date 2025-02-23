from rest_framework import serializers
from .models import Ticket
from core.serializers import CustomUserSerializer

class TicketSerializer(serializers.ModelSerializer):
    customer_details = CustomUserSerializer(source='customer', read_only=True)
    handler_details = CustomUserSerializer(source='handled_by', read_only=True)
    
    class Meta:
        model = Ticket
        fields = [
            'id',
            'title',
            'category', 
            'status', 
            'priority',
            'Message', 
            'Response', 
            'Response_Time', 
            'created_at',
            'customer',
            'customer_details',
            'handled_by',
            'handler_details'
        ]
        read_only_fields = ['id', 'created_at', 'Response_Time', 'customer', 'handled_by']

    def validate_category(self, value):
        if value not in dict(Ticket.TicketCategory.choices):
            raise serializers.ValidationError("Invalid category choice")
        return value

    def validate_status(self, value):
        if value not in dict(Ticket.TicketStatus.choices):
            raise serializers.ValidationError("Invalid status choice")
        return value

    def validate_priority(self, value):
        if value not in dict(Ticket.TicketPriority.choices):
            raise serializers.ValidationError("Invalid priority choice")
        return value
