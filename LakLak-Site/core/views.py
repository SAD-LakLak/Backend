from django.contrib.auth import get_user_model
from rest_framework import generics
from core.serializers import UserSerializer

class UserCreateAPIView(generics.CreateAPIView):
    queryset = get_user_model().objects.all()
    serializer_class = UserSerializer
