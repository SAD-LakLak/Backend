from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

# Create your models here.
class PasswordRecoveryRequest(models.Model):
    user = models.ForeignKey(get_user_model(),on_delete=models.CASCADE)
    token = models.CharField(max_length=64)
    date_created = models.DateTimeField(default=timezone.now)
