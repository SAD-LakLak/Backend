from django.contrib import admin
from .models import Product, ProductImage, Package, PackageReview


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    pass


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    pass

@admin.register(Package)
class PackageAdmin(admin.ModelAdmin):
    pass

@admin.register(PackageReview)
class PackageReviewAdmin(admin.ModelAdmin):
    list_display = ('package', 'user', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('package__name', 'user__username', 'comment')
    readonly_fields = ('created_at',)