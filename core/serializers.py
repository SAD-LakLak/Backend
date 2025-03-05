from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework import serializers
from core import models
from .models import Product, ProductImage, CustomUser, Package, Address
import core.models


class CustomUserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, min_length=8)

    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'first_name', 'last_name', 'password', 'role', 'national_code', 'birth_date', 'phone_number']

    def create(self, validated_data):
        user = CustomUser.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            role=validated_data.get('role', 'customer'),
            national_code=validated_data.get('national_code', ''),
            birth_date=validated_data.get('birth_date', None),
            phone_number=validated_data.get('phone_number', '')
        )
        return user

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        data['role'] = self.user.role  # Include user role in the token payload
        return data


class ProductImageSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = ProductImage
        fields = ['id', 'image_url']

    def get_image_url(self, obj):
        request = self.context.get('request')
        if obj.image and request:
            return request.build_absolute_uri(obj.image.url)
        return None


class ProductSerializer(serializers.ModelSerializer):
    product_images = ProductImageSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = ['id', 'type', 'name', 'info', 'price', 'stock', 'is_active', 'product_images']

class PackageSerializer(serializers.ModelSerializer):
    score = serializers.SerializerMethodField()
    stock = serializers.SerializerMethodField()
    products = serializers.SerializerMethodField()

    class Meta:
        model = Package
        fields = [
            'id', 'name', 'summary', 'description',
            'total_price', 'image', 'products', 'is_active',
            'target_group', 'creation_date', 'score', 'stock',
        ]
    
    def get_score(self, package):
        if package.score_count == 0:
            return "-1"
        return f"{(package.score_sum / package.score_count) : .2f}"
    
    def get_stock(self, package):
        minstock_product = package.products.order_by("stock")[0]
        return minstock_product.stock
    
    def get_products(self, package):
        return [product.name for product in package.products.all()]
    
class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = '__all__'
        extra_kwargs = {'user': {'read_only': True}}  # Make 'user' read-only
    
class OrderPackageSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.OrderPackage
        fields = ['package', 'amount', 'price']

class CustomerOrderSerializer(serializers.ModelSerializer):
    packages = OrderPackageSerializer(many=True, write_only=True)  # Nested for input
    order_status = serializers.CharField(read_only=True)  # Customers can't set this manually

    class Meta:
        model = models.CustomerOrder
        fields = [
            'id', 'user', 'order_status', 'order_date',
            'discount_amount', 'tax_amount', 'shipping_fee',
            'expected_delivery_date_time', 'note', 'discount', 'address',
            'packages'
        ]
        extra_kwargs = {'user': {'read_only':True}}

    def create(self, validated_data):
        packages_data = validated_data.pop('packages')
        order = models.CustomerOrder.objects.create(**validated_data)

        for package_data in packages_data:
            package = package_data['package']
            amount = package_data['amount']
            price = package_data['price']
            models.OrderPackage.objects.create(order=order, package=package, amount=amount, price=price)
        order.save()

        return order


class OrderPackageDetailSerializer(serializers.ModelSerializer):
    package_name = serializers.CharField(source="package.name", read_only=True)  # Assuming Package has a name field
    package_price = serializers.DecimalField(source="package.price", max_digits=10, decimal_places=2, read_only=True)  # Assuming Package has a price field

    class Meta:
        model = models.OrderPackage
        fields = ['package', 'package_name', 'package_price', 'amount']

class CustomerOrderHistorySerializer(serializers.ModelSerializer):
    packages = OrderPackageDetailSerializer(many=True, source='orderpackage_set')  # Retrieve related packages
    order_status = serializers.CharField(read_only=True)

    class Meta:
        model = models.CustomerOrder
        fields = [
            'id', 'order_status', 'order_date',
            'discount_amount', 'tax_amount', 'shipping_fee',
            'expected_delivery_date_time', 'note', 'address', 'packages'
        ]

