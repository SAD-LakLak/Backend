from django.contrib.auth import get_user_model, logout
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404
from django.conf import settings
from django.utils.crypto import get_random_string
from django.urls import reverse
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework.views import APIView
from rest_framework import filters
from core.serializers import UserSerializer, ProductSerializer
from core.models import Product, ProductImage
from core.pagination import ProductPagination
from rest_framework import filters
from core.filters import ProductFilter
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


@api_view(['POST'])
def register_new_product(request):
    try:
        type = request.POST['type']
        if type not in [choice[0] for choice in Product.TYPE_CHOICES]:
            raise ValueError
        name = request.POST['name']
        info = request.POST['description']
        price = request.POST['price']
        stock = request.POST['stock']
    except Exception as e:
        return Response({"success" : "false"}, status.HTTP_400_BAD_REQUEST)
    
    try:
        new_product = Product.objects.create(
            type=type, name=name, info=info, is_active=True, price=price, stock=stock
        )
        return Response({"success" : "true", "id" : new_product.id})
    except:
        return Response({"success" : "false"}, status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
def update_product(request):
    try:
        product = get_object_or_404(Product, pk=request.POST['id'])
        for field, new_value in request.POST.items():
            if field == 'type':
                if new_value in [choice[0] for choice in Product.TYPE_CHOICES]:
                    product.type = new_value
                else:
                    raise ValueError
            if field == 'name':
                product.name = new_value
            if field == 'info':
                product.info = new_value
            if field == 'price':
                product.price = new_value
            if field == 'stock':
                product.stock = new_value
        product.save()
        return Response({"success" : "true"})
    except:
        return Response({"success" : "false"}, status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
def upload_product_image(request):
    if request.FILES and request.FILES.get('image', False):
        try:
            product = get_object_or_404(Product, pk=request.POST['id'])
            uploaded_image = request.FILES['image']
            ProductImage.objects.create(image=uploaded_image, product=product)
            return Response({"success" : "true"})
        except:
            return Response({"success" : "false"}, status.HTTP_500_INTERNAL_SERVER_ERROR)
    else:
        return Response({"success" : "false"}, status.HTTP_400_BAD_REQUEST)

class LogoutAPIView(APIView):
    def post(self, request):
        logout(request)
        return Response(status=status.HTTP_204_NO_CONTENT)


class ProductListAPIView(generics.ListAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    pagination_class = ProductPagination
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter, filters.SearchFilter]
    filterset_class = ProductFilter
    search_fields = ['name', 'info']
    ordering_fields = ['name', 'price', 'creation_date', 'type']
