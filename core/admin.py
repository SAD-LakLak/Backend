from django.contrib import admin
from .models import Product, ProductImage, Package, PackageReview
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser

admin.site.site_header = "LakLak Administration"
admin.site.site_title = "LakLak Admin Panel"
admin.site.index_title = "LakLak Administration"

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'type', 'provider', 'price', 'stock', 'is_active')
    list_filter = ('type', 'is_active', 'provider')
    search_fields = ('name', 'info', 'provider__username')
    ordering = ('name',)


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    pass


@admin.register(Package)
class PackageAdmin(admin.ModelAdmin):
    list_display = ('name', 'target_group', 'total_price', 'is_active')
    list_filter = ('target_group', 'is_active')
    search_fields = ('name', 'description', 'summary')
    filter_horizontal = ('products',)
    readonly_fields = ('creation_date', 'last_modification')


@admin.register(PackageReview)
class PackageReviewAdmin(admin.ModelAdmin):
    list_display = ('package', 'user', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('package__name', 'user__username', 'comment')
    readonly_fields = ('created_at',)


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'role', 'is_staff', 'is_active')
    list_filter = ('role', 'is_staff', 'is_active')
    search_fields = ('username', 'email', 'national_code', 'phone_number')
    ordering = ('username',)

    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal Info',
         {'fields': ('first_name', 'last_name', 'email', 'phone_number', 'national_code', 'birth_date')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important Dates', {'fields': ('last_login', 'date_joined')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'username', 'email', 'password1', 'password2', 'role', 'phone_number', 'national_code', 'is_staff',
                'is_active')}
         ),
    )
