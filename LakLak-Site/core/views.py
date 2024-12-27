from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.conf import settings
from django.utils.crypto import get_random_string

from rest_framework import generics
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view

from core.serializers import UserSerializer
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
        return Response({"message":"No user found with this email"},status=status.HTTP_406_NOT_ACCEPTABLE)
    
    try:
        send_mail('LakLak: Password Reset Request',
                  f"Dear {user.first_name},\nWe are sending this email in response to a password reset request just received for your account.",
                  settings.EMAIL_HOST_USER,
                  [email_address],
                  fail_silently=False,
        )
        # TODO : obtain the infrastructure needed for the above method call to operate properly.
    except Exception as e:
        return Response({"error-message" : str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return Response(
        {"message" : "Password reset email sent successfully. Check you spam folder if it does not appear in several minutes."},
          status=status.HTTP_200_OK
          )

@api_view(['GET', 'POST'])
def reset_password_based_on_token(request, token):
    if request.method == 'GET':
        try:
            reset_request = PasswordRecoveryRequest.objects.get(token=token)
        except:
            return Response({"tokenValidity" : "False"}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"tokenValidity" : "True", "resetToken" : reset_request.token})
    elif request.method == 'POST':
        try:
            reset_request = PasswordRecoveryRequest.objects.get(token=request.POST['resetToken'])
        except:
            return Response({"tokenValidity" : "False"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            user = reset_request.user
            # TODO (optional) : Additional check for validity of the new password (eg its length)
            user.set_password(request.POST['newPassword'])
            return Response({"success" : "True"})
        except:
            return Response({"success" : "False"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
