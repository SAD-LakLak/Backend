from django.db import models
from core.models import CustomUser, CustomerOrder
from django.db import models

class Ticket(models.Model):
    class TicketStatus(models.TextChoices):
        OPEN = 'Open', 'Open'
        IN_PROGRESS = 'In Progress', 'In Progress'
        RESOLVED = 'Resolved', 'Resolved'
        CLOSED = 'Closed', 'Closed'

    class TicketPriority(models.TextChoices):
        LOW = 'Low', 'Low'
        MEDIUM = 'Medium', 'Medium'
        HIGH = 'High', 'High'
        URGENT = 'Urgent', 'Urgent'

    class TicketCategory(models.TextChoices):
        ORDER_ISSUE = 'Order Issue', 'Order Issue'
        PAYMENT_ISSUE = 'Payment Issue', 'Payment Issue'
        TECHNICAL = 'Technical', 'Technical'
        GENERAL = 'General', 'General'
        OTHER = 'Other', 'Other'
    title = models.CharField(max_length=255)
    category = models.CharField(max_length=50, choices=TicketCategory.choices, default=TicketCategory.GENERAL)
    status = models.CharField(max_length=20, choices=TicketStatus.choices, default=TicketStatus.OPEN)
    priority = models.CharField(max_length=10, choices=TicketPriority.choices, default=TicketPriority.MEDIUM)
    Message = models.TextField(max_length=3000, default='Default message')
    Response = models.TextField(null=True, blank=True)
    Response_Time = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    customer = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='customer_tickets')
    handled_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='handled_tickets', null=True, blank=True)

    def __str__(self):
        return f"{self.title} - {self.category} (Customer: {self.customer.first_name})"
