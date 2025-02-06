from django.db import models
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.conf import settings
from django.db.models import Sum
from datetime import timedelta



class CustomUser(AbstractUser):
    ROLE_CHOICES = (
        ('supplier', 'Supplier'),
        ('package_combinator', 'Package Combinator'),
        ('customer', 'Customer'),
        ('delivery_personnel', 'Delivery Personnel'),
        ('supervisor', 'Service Supervisor')
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='customer', blank=True)
    national_code = models.CharField(max_length=20, blank=True)
    birth_date = models.DateTimeField(blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True)


class PasswordRecoveryRequest(models.Model):
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    token = models.CharField(max_length=64)
    date_created = models.DateTimeField(default=timezone.now)

    def has_expired(self):
        return self.date_created < timezone.now() - timedelta(minutes=settings.EMAIL_REQUEST_TTL)

class Product(models.Model):
    TYPE_CHOICES = (
        ('food', 'Food'),
        ('clothing', 'Clothing'),
        ('service', 'Service'),
        ('sanitary', 'Sanitary'),
        ('entertainment', 'Entertainment'),
        ('other', 'Other')
    )
    provider = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    type = models.CharField(max_length=50, choices=TYPE_CHOICES, blank=True)
    name = models.CharField(max_length=255, blank=True)
    info = models.TextField(max_length=5000, blank=True)
    is_active = models.BooleanField(default=False, blank=True)
    is_deleted = models.BooleanField(default=False, blank=True)
    last_update = models.DateTimeField(auto_now=True)
    creation_date = models.DateTimeField(auto_now_add=True)
    price = models.PositiveBigIntegerField(blank=True)
    stock = models.PositiveIntegerField(blank=True)
    images = models.ManyToManyField('ProductImage', blank=True, related_name='products')

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

class ProductImage(models.Model):
    image = models.ImageField(upload_to='product_images/')
    product = models.ForeignKey(Product, related_name='product_images', on_delete=models.CASCADE)

class Package(models.Model):
    AGE_GROUPS = (
        ('pregnants', 'Pregnant Mothers'),
        ('less_6', 'Infants to 6 Months'),
        ('less_12', 'Infants to One Year'),
        ('less_24', 'Infants to Two Years'),
    )
    name = models.CharField(max_length=255)
    products = models.ManyToManyField(Product, related_name='packages')
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    image = models.ImageField(upload_to='package_images/', null=True)
    is_active = models.BooleanField(default=True)
    summary = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)
    target_group = models.CharField(choices=AGE_GROUPS, null=True)
    creation_date = models.DateTimeField(auto_now_add=True)
    last_modification = models.DateTimeField(auto_now=True)
    score_sum = models.BigIntegerField(default=0)
    score_count = models.IntegerField(default=0)

