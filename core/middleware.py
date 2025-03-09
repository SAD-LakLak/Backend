from django.utils.functional import SimpleLazyObject
from django.contrib.auth.middleware import get_user
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.utils.deprecation import MiddlewareMixin
from rest_framework_simplejwt.tokens import AccessToken
from django.contrib.auth import get_user_model
from django.conf import settings
import jwt

def get_user_jwt(request):

    user = None
    try:
        user_jwt = JWTAuthentication().authenticate(request)
        if user_jwt is not None:
            user = user_jwt[0]
    except:
        pass

    return user

class AuthenticationMiddleware(MiddlewareMixin):
    def process_request(self, request):

        assert hasattr(request, 'session'), "The authentication middleware requires session middleware to be installed."
        
        request.user = SimpleLazyObject(lambda: get_user(request))
        
        if not request.user.is_authenticated:
            request.user = SimpleLazyObject(lambda: get_user_jwt(request))