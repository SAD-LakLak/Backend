from django.contrib import admin
from .models import Product, ProductImage, Package


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    pass


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    pass

@admin.register(Package)
class PackageAdmin(admin.ModelAdmin):
    pass
