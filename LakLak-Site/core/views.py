from django.contrib.auth import get_user_model, logout
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404
from django.conf import settings
from django.utils.crypto import get_random_string
from django.urls import reverse
from rest_framework.permissions import AllowAny
from rest_framework import generics, status, viewsets, filters
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework.views import APIView
from rest_framework import filters
from django_filters.rest_framework import DjangoFilterBackend
from core.serializers import UserSerializer, ProductSerializer
from core.models import Product, ProductImage, PasswordRecoveryRequest, CustomUser
from .serializers import RegistrationSerializer
from core.pagination import ProductPagination
from core.filters import ProductFilter


class RegistrationView(generics.CreateAPIView):
    queryset = CustomUser.objects.all()
    serializer_class = RegistrationSerializer
    permission_classes = [AllowAny]  # Allow anyone to access this endpoint

def failure_response(message, status=status.HTTP_400_BAD_REQUEST):
    return Response({"success" : "false", "message" : message}, status=status)

@api_view(['POST'])
def send_password_recovery_email(request):
    email_address = request.POST['email']
    try:
        user = get_user_model().objects.get(email=email_address)
    except:
        return failure_response("No user found with this email", status=status.HTTP_406_NOT_ACCEPTABLE)

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
        return failure_response(str(e), status=status.HTTP_500_INTERNAL_SERVER_ERROR)

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
        return failure_response(str(e))
    
    try:
        new_product = Product.objects.create(
            type=type, name=name, info=info, is_active=True, price=price, stock=stock
        )
        return Response({"success" : "true", "id" : new_product.id})
    except Exception as e:
        return failure_response(str(e))

@api_view(['POST'])
def update_product(request):
    product = get_object_or_404(Product, pk=request.POST['id'])
    for field, new_value in request.POST.items():
        if field == 'type':
            if new_value in [choice[0] for choice in Product.TYPE_CHOICES]:
                product.type = new_value
            else:
                return failure_response('invalid type')
        elif field == 'name':
            if new_value == '':
                return failure_response('empty name')
            product.name = new_value
        elif field == 'info':
            product.info = new_value
        elif field == 'price':
            try:
                product.price = int(new_value)
            except:
                return failure_response('non-integer value')
            if int(new_value) < 0:
                return failure_response('negative price')
        elif field == 'stock':
            try:
                product.stock = int(new_value)
            except:
                return failure_response('non-integer stock')
            if int(new_value) < 0:
                return failure_response('negative stock')
        elif field == 'active':
            if new_value == 'true':
                product.is_active = True
            elif new_value == 'false':
                product.is_active = False
            else:
                return failure_response('invalid active state')
        else:
            return failure_response('unsupported field for change: ' + field)
    product.save()
    return Response({"success" : "true"})

@api_view(['POST'])
def upload_product_image(request):
    if request.FILES and request.FILES.get('image', False):
        try:
            product = get_object_or_404(Product, pk=request.POST['id'])
            uploaded_image = request.FILES['image']
            ProductImage.objects.create(image=uploaded_image, product=product)
            return Response({"success" : "true"})
        except Exception as e:
            return failure_response(str(e), status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    else:
        return failure_response('no image provided')

@api_view(['DELETE'])
def delete_product(request, product_id):
    try:
        product = get_object_or_404(Product, pk=product_id)
        product.is_deleted = True
        product_id.save()
    except:
        return failure_response('server error', status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class LogoutAPIView(APIView):
    def post(self, request):
        logout(request)
        return Response(status=status.HTTP_204_NO_CONTENT)

class ProductListAPIView(generics.ListAPIView):
    queryset = Product.objects.filter(is_deleted=False)
    serializer_class = ProductSerializer
    pagination_class = ProductPagination
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter, filters.SearchFilter]
    filterset_class = ProductFilter
    search_fields = ['name', 'info']
    ordering_fields = ['name', 'price', 'creation_date', 'type']
