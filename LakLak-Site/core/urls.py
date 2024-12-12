from django.urls import path
from core import views


urlpatterns = [
    path('register/', views.UserCreateAPIView.as_view(), name='user-register'),

]