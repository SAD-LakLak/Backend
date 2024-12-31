from django.urls import path
from core import views
from .serializers import CustomTokenObtainPairSerializer
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)


urlpatterns = [
    path('register/', views.RegistrationView.as_view(), name='register'),
    path('api/token/', TokenObtainPairView.as_view(serializer_class=CustomTokenObtainPairSerializer), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('reset_password/', views.send_password_recovery_email, name='send_password_email'),
    path('reset_password/<str:token>', views.reset_password_based_on_token, name='reset_with_token'),
    path('logout/', views.LogoutAPIView.as_view(), name='logout'),
    path('products/register/', views.register_new_product, name='product-register'),
    path('products/update/', views.update_product, name='product-update'),
    path('products/image/', views.upload_product_image, name='product-image'),
    path('products/delete/<int:product_id>/', views.delete_product, name='product-delete'),
    path('products/', views.ProductListAPIView.as_view(), name='product-list'),
]