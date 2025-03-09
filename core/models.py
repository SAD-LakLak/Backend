from django.db import models
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.conf import settings
from datetime import timedelta
from django.core.validators import MinValueValidator, MaxValueValidator


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
    avatar_url = models.URLField(max_length=500, blank=True, null=True)  # Add avatar URL field

    def get_avatar(self):
        return self.avatar_url if self.avatar_url else None


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

    def __str__(self):
        return f"{self.name} ({self.type}) - Stock: {self.stock}"


class ProductImage(models.Model):
    image = models.ImageField(upload_to='product_images/')
    product = models.ForeignKey(Product, related_name='product_images', on_delete=models.CASCADE)

class UserFile(models.Model):
    user = models.ForeignKey(CustomUser, related_name='user_files', on_delete=models.CASCADE)
    file = models.FileField(upload_to='user_files/')
    tag = models.CharField(max_length=255, null=False, blank=False)


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

class Discount(models.Model):
    DISCOUNT_TYPES = (
        ('percent', 'Pencent Discount'),
        ('fixed', 'Fixed Discount')
    )
    code = models.CharField(max_length=50)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    is_used = models.BooleanField(default=False)
    type = models.CharField(max_length=10, choices=DISCOUNT_TYPES)

from django.db import models
from django.contrib.auth import get_user_model

class Address(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='addresses')
    address_line_1 = models.CharField(max_length=255)
    address_line_2 = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    country = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    is_default = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if self.is_default:
            # Unset previous default address for the same user
            Address.objects.filter(user=self.user, is_default=True).exclude(id=self.id).update(is_default=False)
        
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Address - {self.city}, {self.state}"



class CustomerOrder(models.Model):
    class OrderStatus(models.TextChoices):
        PENDING = 'Pending', 'Pending'
        PROCESSING = 'Processing', 'Processing'
        SHIPPED = 'Shipped', 'Shipped'
        DELIVERED = 'Delivered', 'Delivered'
        CANCELLED = 'Cancelled', 'Cancelled'
        RETURNED = 'Returned', 'Returned'

    user = models.ForeignKey('CustomUser', on_delete=models.CASCADE, related_name="orders")
    order_status = models.CharField(max_length=20, choices=OrderStatus.choices, default=OrderStatus.PENDING)
    order_date = models.DateTimeField(auto_now_add=True)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    shipping_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    expected_delivery_date_time = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    note = models.TextField(blank=True, null=True)

    discount = models.ForeignKey('Discount', on_delete=models.SET_NULL, null=True, blank=True)
    address = models.ForeignKey('Address', on_delete=models.CASCADE)

    packages = models.ManyToManyField('Package', through='OrderPackage')
    is_deleted = models.BooleanField(default=False)

    def __str__(self):
        return f"Order {self.id} - {self.user}"

class OrderPackage(models.Model):
    order = models.ForeignKey(CustomerOrder, on_delete=models.CASCADE)
    package = models.ForeignKey('Package', on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    amount = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('order', 'package')

    def __str__(self):
        return f"{self.amount}x {self.package} in Order {self.order.id}"
    

class PackageReview(models.Model):
    package = models.ForeignKey(Package, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='package_reviews')
    rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('package', 'user')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Review by {self.user.username} for {self.package.name}: {self.rating}/5"
    
    def save(self, *args, **kwargs):
        is_new = self.pk is None
        
        if not is_new:
            old_instance = PackageReview.objects.get(pk=self.pk)
            old_rating = old_instance.rating
        
        super().save(*args, **kwargs)
        
        if is_new:
            self.package.score_sum += self.rating
            self.package.score_count += 1
        else:
            self.package.score_sum = self.package.score_sum - old_rating + self.rating
        
        self.package.save()
    
    def delete(self, *args, **kwargs):
        self.package.score_sum -= self.rating
        self.package.score_count -= 1
        self.package.save()
        
        super().delete(*args, **kwargs)