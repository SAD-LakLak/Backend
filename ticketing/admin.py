from django.contrib import admin
from .models import Ticket
from django.contrib.admin import SimpleListFilter

class CustomerRoleFilter(SimpleListFilter):
    title = 'Customer Role'
    parameter_name = 'customer_role'

    def lookups(self, request, model_admin):
        return (
            ('supplier', 'Supplier'),
            ('customer', 'Customer'),
            ('package_combinator', 'Package Combinator'),
            ('delivery_personnel', 'Delivery Personnel'),
            ('supervisor', 'Service Supervisor'),
        )

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(customer__role=self.value())
        return queryset

@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'status', 'priority', 'customer', 'handled_by', 'created_at')
    list_filter = ('status', 'priority', 'category', 'created_at', CustomerRoleFilter)
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
