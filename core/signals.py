from django.db.models.signals import post_save, m2m_changed
from django.dispatch import receiver
from .models import Product, Package
from django.db.models import Sum

@receiver(m2m_changed, sender=Package.products.through)
def update_total_price(sender, instance, action, **kwargs):
    if action in ['post_add', 'post_remove', 'post_clear']:
        total_price = instance.products.aggregate(total_price=Sum('price'))['total_price'] or 0
        instance.total_price = total_price
        instance.save()

@receiver(post_save, sender=Product)
def update_package_total_price_on_product_save(sender, instance, **kwargs):
    packages = Package.objects.filter(products=instance)
    for package in packages:
        total_price = package.products.aggregate(total_price=Sum('price'))['total_price'] or 0
        package.total_price = total_price
        package.save()