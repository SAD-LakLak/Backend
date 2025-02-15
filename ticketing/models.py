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

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="tickets")
    subject = models.CharField(max_length=255)
    category = models.CharField(max_length=50, choices=TicketCategory.choices, default=TicketCategory.GENERAL)
    status = models.CharField(max_length=20, choices=TicketStatus.choices, default=TicketStatus.OPEN)
    priority = models.CharField(max_length=10, choices=TicketPriority.choices, default=TicketPriority.MEDIUM)

    order = models.ForeignKey(CustomerOrder, on_delete=models.SET_NULL, null=True, blank=True, related_name="tickets")
    assigned_to = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name="assigned_tickets")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Ticket {self.id} - {self.subject} ({self.status})"

class TicketMessage(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name="messages")
    sender = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="ticket_messages")
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Message on Ticket {self.ticket.id} by {self.sender.username}"

class TicketAttachment(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name="attachments")
    uploaded_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="ticket_attachments")
    file = models.FileField(upload_to="ticket_attachments/")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Attachment for Ticket {self.ticket.id} by {self.uploaded_by.username}"

class TicketStatusLog(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name="status_logs")
    changed_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    previous_status = models.CharField(max_length=20, choices=Ticket.TicketStatus.choices)
    new_status = models.CharField(max_length=20, choices=Ticket.TicketStatus.choices)
    changed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Status change for Ticket {self.ticket.id} - {self.previous_status} → {self.new_status}"
