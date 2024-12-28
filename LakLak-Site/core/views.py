from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.conf import settings
from django.utils.crypto import get_random_string
from django.urls import reverse

from rest_framework import generics
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view

from core.serializers import UserSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import logout
from .models import PasswordRecoveryRequest

class UserCreateAPIView(generics.CreateAPIView):
    queryset = get_user_model().objects.all()
    serializer_class = UserSerializer

@api_view(['POST'])
def send_password_recovery_email(request):
    email_address = request.POST['email']
    try:
        user = get_user_model().objects.get(email=email_address)
    except:
        return Response({"success" : "false", "message":"No user found with this email"},status=status.HTTP_406_NOT_ACCEPTABLE)
    
    # Delete any remained reset requests for this user from past, if any
    PasswordRecoveryRequest.objects.filter(user=user).delete()

    try:
        new_recovery_request = PasswordRecoveryRequest.objects.create(user=user, token=get_random_string(64))
        content = settings.EMAIL_RECOVERY_TEMPLATE.format(
            name=user.username,
            reset_link=reverse('core:reset_with_token', args=(new_recovery_request.token,))
        )
        send_mail('LakLak: Password Reset Request',
                  content,
                  settings.EMAIL_FROM_ADDRESS,
                  [email_address],
                  fail_silently=False,
        )
    except Exception as e:
        return Response({"success" : "false", "message" : str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return Response(
        {"success" : "True"},
          status=status.HTTP_200_OK
          )

@api_view(['GET', 'POST'])
def reset_password_based_on_token(request, token):
    try:
        reset_request = PasswordRecoveryRequest.objects.get(token=token)
        if reset_request.has_expired():
            reset_request.delete()
            raise Exception("Expired Token")
    except:
        return Response({"tokenValidity" : "False"}, status=status.HTTP_400_BAD_REQUEST)
    if request.method == 'GET':
        return Response({"tokenValidity" : "True", "resetToken" : reset_request.token})
    elif request.method == 'POST':
        try:
            user = reset_request.user
            # TODO (optional) : Additional check for validity of the new password (eg its length)            
            user.set_password(request.POST['newPassword'])
            user.save()
            reset_request.delete()
            return Response({"success" : "True"})
        except:
            return Response({"success" : "False"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class LogoutAPIView(APIView):
    def post(self, request):
        logout(request)
        return Response(status=status.HTTP_204_NO_CONTENT)