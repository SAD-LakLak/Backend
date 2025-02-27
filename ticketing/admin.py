from django.contrib import admin
from .models import Ticket

@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'status', 'priority', 'customer', 'handled_by', 'created_at')
    list_filter = ('status', 'priority', 'category', 'created_at')
    search_fields = ('title', 'customer__email', 'customer__first_name', 'customer__last_name')
    readonly_fields = ('created_at',)
    list_per_page = 20
    
    fieldsets = (
        ('Ticket Information', {
            'fields': ('title', 'category', 'status', 'priority', 'Message')
        }),
        ('Response', {
            'fields': ('Response', 'Response_Time')
        }),
        ('Customer Information', {
            'fields': ('customer', 'handled_by')
        }),
        ('Timestamps', {
            'fields': ('created_at',)
        }),
    )
