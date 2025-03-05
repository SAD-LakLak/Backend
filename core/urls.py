from django.urls import path, include
from core import views
from .serializers import CustomTokenObtainPairSerializer
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

app_name = 'core'
urlpatterns = [
    path('register/', views.RegistrationView.as_view(), name='register'),
    path('user/', views.GetUserByTokenView.as_view(), name='get_user_by_token'),
    path('api/token/', TokenObtainPairView.as_view(serializer_class=CustomTokenObtainPairSerializer), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('reset_password/', views.send_password_recovery_email, name='send_password_email'),
    path('reset_password/<str:token>', views.reset_password_based_on_token, name='reset_with_token'),
    path('logout/', views.LogoutAPIView.as_view(), name='logout'),
    path('products/register/', views.register_new_product, name='product-register'),
    path('products/update/bulk/granular/', views.granular_bulk_stock_change, name='granular-bulk-change'),
    path('products/update/bulk/', views.bulk_stock_change, name='bulk-update'),
    path('products/update/', views.update_product, name='product-update'),
    path('products/image/', views.upload_product_image, name='product-image'),
    path('products/delete/images/<int:image_id>', views.delete_product_image, name='image-delete'),
    path('products/delete/<int:product_id>/', views.delete_product, name='product-delete'),
    path('products/', views.ProductListAPIView.as_view(), name='product-list'),
    path('packages/', views.PackageListAPIView.as_view(), name='package-list'),
    path('packages/<int:pk>/', views.PackageDetailAPIView.as_view(), name='package-detail'),
    path('', include('ticketing.urls')),
    path('addresses/', views.AddressListView.as_view(), name='address-list'),
    path('addresses/<int:pk>/', views.AddressDetailView.as_view(), name='address-detail'),
    path('orders/create/', views.CreateCustomerOrderView.as_view(), name='create-order'),
    path('orders/history/', views.UserOrderHistoryView.as_view(), name='order-history'),
]