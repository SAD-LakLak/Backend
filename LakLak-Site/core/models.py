from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.conf import settings
from datetime import timedelta

# Create your models here.
class PasswordRecoveryRequest(models.Model):
    user = models.ForeignKey(get_user_model(),on_delete=models.CASCADE)
    token = models.CharField(max_length=64)
    date_created = models.DateTimeField(default=timezone.now)

    def has_expired(self):
        return self.date_created < timezone.now() - timedelta(minutes=settings.EMAIL_REQUEST_TTL)
