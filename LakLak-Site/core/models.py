from django.db import models
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.conf import settings
from datetime import timedelta

# Create your models here.
class Product(models.Model):
    TYPE_CHOICES = (
        ('edible', 'Edible Products'),
        ('clothing', 'Clothing'),
        ('toiletries', 'Toiletries')
    )
    name = models.CharField(max_length=255)
    info = models.TextField(max_length=5000)
    is_active = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)
    last_update = models.DateTimeField(auto_now=True)
    creation_date = models.DateTimeField(auto_created=True)
    price = models.PositiveBigIntegerField()
    stock = models.PositiveIntegerField()


    groups = models.ManyToManyField(
        Group,
        related_name='customuser_groups',  # Ensure a unique related_name
        blank=True,
    )
    user_permissions = models.ManyToManyField(
        Permission,
        related_name='customuser_permissions',  # Ensure a unique related_name
        blank=True,
    )


class CustomUser(AbstractUser):
    ROLE_CHOICES = (
        ('supplier', 'Supplier'),
        ('package_combinator', 'Package Combinator'),
        ('customer', 'Customer'),
        ('delivery_personnel', 'Delivery Personnel'),
        ('supervisor', 'Service Supervisor')
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='customer')
    national_code = models.CharField(max_length=20)
    birth_date = models.DateTimeField()
    phone_number = models.CharField(max_length=20)


# Create your models here.
class PasswordRecoveryRequest(models.Model):
    user = models.ForeignKey(get_user_model(),on_delete=models.CASCADE)
    token = models.CharField(max_length=64)
    date_created = models.DateTimeField(default=timezone.now)

    def has_expired(self):
        return self.date_created < timezone.now() - timedelta(minutes=settings.EMAIL_REQUEST_TTL)
