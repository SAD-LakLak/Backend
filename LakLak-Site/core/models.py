from django.db import models
from django.contrib.auth.models import AbstractUser

# Create your models here.
class Product(models.Model):
    TYPE_CHOICES = (
        ('edible', 'Edible Products'),
        ('clothing', 'Clothing'),
        ('toiletries', 'Toiletries')
    )
    name = models.CharField(max_length=255)
    info = models.TextField(max_length=5000)
    amount = models.IntegerField()
    is_active = models.BooleanField()
    is_deleted = models.BooleanField()
    last_update = models.DateTimeField(auto_now=True)
    creation_date = models.DateTimeField(auto_created=True)
    price = models.PositiveBigIntegerField()
    stock = models.PositiveIntegerField()


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

