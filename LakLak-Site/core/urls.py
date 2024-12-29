from django.urls import path
from core import views
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

app_name = 'core'
urlpatterns = [
    path('register/', views.UserCreateAPIView.as_view(), name='user-register'),
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('reset_password/', views.send_password_recovery_email, name='send_password_email'),
    path('reset_password/<str:token>', views.reset_password_based_on_token, name='reset_with_token'),
    path('logout/', views.LogoutAPIView.as_view(), name='logout'),
]