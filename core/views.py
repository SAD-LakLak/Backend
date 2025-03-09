import logging
from json import loads as parse_json
from django.contrib.auth import get_user_model, logout
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404, redirect, render
from django.conf import settings
from django.utils.crypto import get_random_string
from django.urls import reverse
from rest_framework.permissions import AllowAny
from rest_framework import generics, status, filters
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.views import APIView
from rest_framework import filters, serializers
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from core.serializers import ProductSerializer
from core import serializers
from core import models
from core.models import (
    Product,
    ProductImage,
    PasswordRecoveryRequest,
    CustomUser,
    Package,
    Address,
    PackageReview,
    UserFile,
)
from .serializers import CustomUserSerializer, PackageSerializer, AddressSerializer, CustomTokenObtainPairSerializer
from core.pagination import ProductPagination
from core.filters import ProductFilter, PackageFilter
from core.permissions import *
from django.db.models import F, Case, When, Value, FloatField
from django.http import Http404, HttpResponseRedirect, FileResponse
from rest_framework import viewsets, mixins
from .serializers import PackageReviewSerializer
from .permissions import IsCustomer
from social_django.utils import psa
from rest_framework_simplejwt.tokens import RefreshToken
import requests

logger = logging.getLogger(__name__)

try:
    from inventory.kafka_utils import (
        send_inventory_update, send_price_change_event,
        send_product_created_event, send_product_deleted_event
    )
    KAFKA_AVAILABLE = True
except ImportError:
    KAFKA_AVAILABLE = False

class RegistrationView(generics.CreateAPIView):
    queryset = CustomUser.objects.all()
    serializer_class = CustomUserSerializer
    permission_classes = [AllowAny]  # Allow anyone to access this endpoint

class GetUserByTokenView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        user = request.user
        try:
            serializer = CustomUserSerializer(user)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except CustomUser.DoesNotExist:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)


def failure_response(message, status=status.HTTP_400_BAD_REQUEST):
    return Response({"success" : "false", "message" : message}, status=status)

@api_view(['POST'])
def send_password_recovery_email(request):
    try:
        email_address = parse_json(request.body)['email']
    except:
        return failure_response("No email provided")
    
    user = get_object_or_404(CustomUser, email=email_address)

    # Delete any remained reset requests for this user from past, if any
    PasswordRecoveryRequest.objects.filter(user=user).delete()

    try:
        new_recovery_request = PasswordRecoveryRequest.objects.create(user=user, token=get_random_string(64))
        content = settings.EMAIL_RECOVERY_TEMPLATE.format(
            name=user.username,
            reset_link=settings.EMAIL_DOMAIN_OF_LINK + reverse(
                'core:reset_with_token',
                args=(new_recovery_request.token,),
            ),
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
        {"success" : "true"},
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
        return Response({"tokenValidity" : "false"})
    if request.method == 'GET':
        return Response({"tokenValidity" : "true", "resetToken" : reset_request.token})
    elif request.method == 'POST':
        try:
            new_password = parse_json(request.body)['new_password']
        except:
            return failure_response("No password provided")
        try:
            user = reset_request.user
            # TODO (optional) : Additional check for validity of the new password (eg its length)            
            user.set_password(new_password)
            user.save()
            reset_request.delete()
            return Response({"success" : "true"})
        except:
            return failure_response("server error", status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsSupplier])
def register_new_product(request):
    try:
        data = parse_json(request.body)
        type = data['type']
        if type not in [choice[0] for choice in Product.TYPE_CHOICES]:
            raise ValueError
        name = data['name']
        info = data['description']
        price = data['price']
        stock = data['stock']
        provider = request.user
    except Exception as e:
        return failure_response(str(e))
    
    try:
        new_product = Product.objects.create(
            type=type, name=name, info=info, is_active=True, price=price, stock=stock, provider=provider
        )
        
        if KAFKA_AVAILABLE:
            try:
                product_data = {
                    'name': new_product.name,
                    'type': new_product.type,
                    'price': new_product.price,
                    'stock': new_product.stock,
                    'provider_id': new_product.provider_id
                }
                send_product_created_event(new_product.id, product_data, request.user.id)
            except Exception as e:
                logger.error(f"Failed to send product created event: {str(e)}")
        
        return Response({"success" : "true", "id" : new_product.id})
    except Exception as e:
        return failure_response("server error: " + str(e))

@api_view(['POST'])
@permission_classes([IsSupplier])
def update_product(request):
    try:
        data = parse_json(request.body)
    except:
        return failure_response("invalid data format")
    if data.get('id', None) is None:
        return failure_response("id not provided")
    product = get_object_or_404(Product, pk=data['id'])
    
    old_price = product.price
    old_stock = product.stock
    
    for field, new_value in data.items():
        if field == 'id':
            continue
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
    try:
        product.save()
        
        if KAFKA_AVAILABLE:
            try:
                if old_price != product.price:
                    send_price_change_event(product.id, old_price, product.price, request.user.id)
                
                if old_stock != product.stock:
                    send_inventory_update(product.id, old_stock, product.stock, request.user.id)
            except Exception as e:
                logger.error(f"Failed to send product update events: {str(e)}")
        
        return Response({"success" : "true"})
    except:
        return failure_response("server error", status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsSupplier])
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
@permission_classes([IsSupplier])
def delete_product_image(request, image_id):
    try:
        image = get_object_or_404(ProductImage, pk=image_id)
        provider = image.product.provider
        if (provider != request.user):
            return failure_response("you do not own that product")
        image.delete()
        return Response({"success" : "true"})
    except:
        return failure_response('server error', status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['DELETE'])
@permission_classes([IsSupplier])
def delete_product(request, product_id):
    try:
        product = Product.objects.get(pk=product_id, provider=request.user, is_deleted=False)
    except:
        return failure_response("no such object exists", status=status.HTTP_404_NOT_FOUND)
    try:
        if KAFKA_AVAILABLE:
            try:
                product_data = {
                    'name': product.name,
                    'type': product.type,
                    'price': product.price,
                    'stock': product.stock,
                    'provider_id': product.provider_id
                }
                send_product_deleted_event(product_id, product_data, request.user.id)
            except Exception as e:
                logger.error(f"Failed to send product deleted event: {str(e)}")
        
        product.is_deleted = True
        product.save()
        return Response({"success" : "true"})
    except:
        return failure_response('server error', status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([IsSupplier])
def bulk_stock_change(request):
    provider_id = request.user
    try:
        delta = int(parse_json(request.body)['delta'])
    except Exception as e:
        return failure_response('not provided: ' + str(e))
    try:
        products_before = None
        if KAFKA_AVAILABLE:
            products_before = list(Product.objects.filter(provider_id=provider_id).values('id', 'stock'))
        
        if delta > 0:
            Product.objects.filter(provider_id=provider_id).update(stock=F("stock")+delta)
        else:
            Product.objects\
                .filter(provider_id=provider_id, stock__gt=-delta)\
                .update(stock=F("stock")+delta)
            Product.objects\
                .filter(provider_id=provider_id, stock__lte=-delta)\
                .update(stock=0)
        
        if KAFKA_AVAILABLE and products_before:
            products_after = list(Product.objects.filter(provider_id=provider_id).values('id', 'stock'))
            products_after_dict = {p['id']: p['stock'] for p in products_after}
            
            for product in products_before:
                product_id = product['id']
                old_stock = product['stock']
                new_stock = products_after_dict.get(product_id)
                
                if old_stock != new_stock:
                    try:
                        send_inventory_update(product_id, old_stock, new_stock, provider_id.id)
                    except Exception as e:
                        logger.error(f"Failed to send inventory update for product {product_id}: {str(e)}")
        
        return Response({"success" : "true"})
    except Exception as e:
        logger.error(f"Error in bulk_stock_change: {str(e)}")
        return failure_response('server error', status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    

@api_view(['POST'])
@permission_classes([IsSupplier])
def granular_bulk_stock_change(request):
    provider = request.user
    try:
        data = parse_json(request.body)
        if data.get('ids', None) is None:
            return failure_response("id list not provided")
        if data.get('delta', None) is None:
            return failure_response("delta not provided")
    except:
        return failure_response("invalid data format")
    try:
        product_ids = list(map(int, data['ids'].split('-')))
    except:
        return failure_response('invalid id list')
    try:
        delta = int(data['delta'])
    except:
        return failure_response('invalid delta')
    try:
        products_before = None
        if KAFKA_AVAILABLE:
            products_before = list(Product.objects.filter(pk__in=product_ids, provider=provider).values('id', 'stock'))
        
        if (delta > 0):
            Product.objects\
                .filter(pk__in=product_ids, provider=provider)\
                .update(stock=F("stock")+delta)
        if (delta < 0):
            Product.objects\
                .filter(pk__in=product_ids, provider=provider, stock__gt=-delta)\
                .update(stock=F("stock")+delta)
            Product.objects\
            .filter(pk__in=product_ids, provider=provider, stock__lte=-delta)\
            .update(stock=0)
        
        if KAFKA_AVAILABLE and products_before:
            products_after = list(Product.objects.filter(pk__in=product_ids, provider=provider).values('id', 'stock'))
            products_after_dict = {p['id']: p['stock'] for p in products_after}
            
            for product in products_before:
                product_id = product['id']
                old_stock = product['stock']
                new_stock = products_after_dict.get(product_id)
                
                if old_stock != new_stock:
                    try:
                        send_inventory_update(product_id, old_stock, new_stock, provider.id)
                    except Exception as e:
                        logger.error(f"Failed to send inventory update for product {product_id}: {str(e)}")
        
        return Response({"success" : "true"})
    except Exception as e:
        logger.error(f"Error in granular_bulk_stock_change: {str(e)}")
        return failure_response('server error', status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    

class LogoutAPIView(APIView):
    def post(self, request):
        logout(request)
        return Response(status=status.HTTP_204_NO_CONTENT)

class ProductListAPIView(generics.ListAPIView):
    serializer_class = ProductSerializer
    pagination_class = ProductPagination
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter, filters.SearchFilter]
    filterset_class = ProductFilter
    search_fields = ['name', 'info']
    ordering_fields = ['name', 'price', 'creation_date', 'type']

    def get_queryset(self):
        if not self.request.user.is_authenticated:
            raise serializers.ValidationError("You must be a provider to view products.")
        queryset = Product.objects.filter(provider=self.request.user, is_deleted=False)
        if not queryset.exists():
            raise serializers.ValidationError("This provider does not have any products.")
        return queryset

class PackageListAPIView(generics.ListAPIView):
    serializer_class = PackageSerializer
    pagination_class = ProductPagination
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter, filters.SearchFilter]
    filterset_class = PackageFilter
    search_fields = ['name', 'products__name']
    ordering_fields = ['name', 'id', 'total_price', 'creation_date', 'score_sum']
    
    def get_queryset(self):
        queryset = Package.objects.all()
        queryset = queryset.annotate(
            score=Case(
                When(score_count=0, then=Value(-1)),
                default=F('score_sum') * 1.0 / F('score_count'),
                output_field=FloatField(),
            )
        )
        return queryset

class PackageReviewViewSet(mixins.CreateModelMixin,
                          mixins.UpdateModelMixin,
                          mixins.DestroyModelMixin,
                          viewsets.GenericViewSet):

    queryset = PackageReview.objects.all()
    serializer_class = PackageReviewSerializer
    permission_classes = [IsAuthenticated & IsCustomer]
    
    def get_queryset(self):
        return PackageReview.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    def perform_update(self, serializer):
        serializer.save()

class PackageDetailAPIView(generics.RetrieveAPIView):
    queryset = Package.objects.all()
    serializer_class = PackageSerializer
    lookup_field = 'pk'
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context
    
    def get(self, request, *args, **kwargs):
        try:
            return self.retrieve(request, *args, **kwargs)
        except Http404:
            return Response(
                {"detail": "Package not found."}, 
                status=status.HTTP_404_NOT_FOUND
            )

class AddressListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        addresses = Address.objects.filter(user=request.user)  # Filter by user
        serializer = AddressSerializer(addresses, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = AddressSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)  # Save with the logged-in user
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AddressDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, pk):
        try:
            return Address.objects.get(pk=pk, user=self.request.user)  # Ensure address belongs to the user
        except Address.DoesNotExist:
            raise Http404  

    def get(self, request, pk):
        address = self.get_object(pk)
        serializer = AddressSerializer(address)
        return Response(serializer.data)

    def put(self, request, pk):
        address = self.get_object(pk)
        serializer = AddressSerializer(address, data=request.data, partial=True)  # Allow partial updates
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        address = self.get_object(pk)
        address.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class CreateCustomerOrderView(generics.CreateAPIView):
    serializer_class = serializers.CustomerOrderSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer_class):
        serializer_class.save(user=self.request.user)  # Assign current user to order


class UserOrderHistoryView(generics.ListAPIView):
    serializer_class = serializers.CustomerOrderHistorySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return models.CustomerOrder.objects.filter(user=self.request.user).order_by('-order_date')

# New OAuth related views
class GoogleLoginView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):

        next_url = request.query_params.get('next', settings.SOCIAL_AUTH_LOGIN_REDIRECT_URL)
        auth_url = f"{request.build_absolute_uri('/')[:-1]}/auth/login/google-oauth2/?next={next_url}"
        return Response({'auth_url': auth_url}, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([AllowAny])
@psa('social:complete')
def oauth_complete(request, backend, *args, **kwargs):

    try:
        redirect_uri = request.GET.get('next') or request.session.get('redirect_uri') or settings.SOCIAL_AUTH_LOGIN_REDIRECT_URL
        
        user = request.backend.do_auth(request.GET.get('code'))
        
        if not user:
            return Response({'error': 'Failed to authenticate user'}, status=status.HTTP_400_BAD_REQUEST)
            
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)
        
        if 'api' in request.GET.get('next', ''):
            return Response({
                'access': access_token,
                'refresh': refresh_token,
                'user': CustomUserSerializer(user).data
            }, status=status.HTTP_200_OK)
        else:
            success_url = reverse('core:oauth_success')
            redirect_url = f"{success_url}?access_token={access_token}&refresh_token={refresh_token}&redirect_to={redirect_uri}"
            return HttpResponseRedirect(redirect_url)
            
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class GoogleLoginCallbackView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):

        code = request.query_params.get('code')
        if not code:
            return Response({'error': 'Authorization code is missing'}, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            token_url = "https://oauth2.googleapis.com/token"
            data = {
                'code': code,
                'client_id': settings.SOCIAL_AUTH_GOOGLE_OAUTH2_KEY,
                'client_secret': settings.SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET,
                'redirect_uri': request.build_absolute_uri('/complete/google-oauth2/'),
                'grant_type': 'authorization_code',
            }
            
            response = requests.post(token_url, data=data)
            token_data = response.json()
            
            user_info_url = "https://www.googleapis.com/oauth2/v3/userinfo"
            headers = {'Authorization': f"Bearer {token_data.get('access_token')}"}
            user_info_response = requests.get(user_info_url, headers=headers)
            user_info = user_info_response.json()
            
            try:
                user = CustomUser.objects.get(email=user_info.get('email'))
                created = False
            except CustomUser.DoesNotExist:
                username = user_info.get('email').split('@')[0]
                base_username = username
                counter = 1
                while CustomUser.objects.filter(username=username).exists():
                    username = f"{base_username}{counter}"
                    counter += 1


                user = CustomUser.objects.create_user(
                    username=username,
                    email=user_info.get('email'),
                    password=get_random_string(32),
                    first_name=user_info.get('given_name', ''),
                    last_name=user_info.get('family_name', ''),
                    role='customer',
                    avatar_url=user_info.get('picture', '')
                )
                created = True
            
            if not created:
                update_fields = []
                if not user.first_name and user_info.get('given_name'):
                    user.first_name = user_info.get('given_name')
                    update_fields.append('first_name')
                if not user.last_name and user_info.get('family_name'):
                    user.last_name = user_info.get('family_name')
                    update_fields.append('last_name')
                if not user.avatar_url and user_info.get('picture'):
                    user.avatar_url = user_info.get('picture')
                    update_fields.append('avatar_url')
                if update_fields:
                    user.save(update_fields=update_fields)
            
            refresh = RefreshToken.for_user(user)
            token_data = {
                'access': str(refresh.access_token),
                'refresh': str(refresh),
                'user': CustomUserSerializer(user).data,
                'is_new_user': created
            }
            
            redirect_to = request.query_params.get('redirect_to')
            if redirect_to and redirect_to in settings.SOCIAL_AUTH_ALLOWED_REDIRECT_HOSTS:
                redirect_url = f"{redirect_to}?access_token={token_data['access']}&refresh_token={token_data['refresh']}"
                return HttpResponseRedirect(redirect_url)
                
            return Response(token_data, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([IsSupplier])
def upload_user_file(request):
    if request.FILES and request.FILES.get('file', False) and request.POST.get('tag', False):
        try:
            uploaded_file = request.FILES['file']
            tag = request.POST['tag']
            if tag == "":
                return failure_response("empty tag", status=status.HTTP_400_BAD_REQUEST)
            UserFile.objects.create(file=uploaded_file, user=request.user, tag=tag)
            return Response({"success" : "true"})
        except Exception as e:
            return failure_response(str(e), status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    else:
        return failure_response('no file provided')

@api_view(['GET'])
@permission_classes([IsSupplier])
def get_user_file(request, tag):
    try:
        user_file = UserFile.objects.get(user=request.user, tag=tag)
    except:
        return failure_response(f"user has no file with tag {tag}", status=status.HTTP_400_BAD_REQUEST)
    
    response = FileResponse(user_file.file.open())
    response['Content-Type'] = 'application/pdf'
    response['Content-Disposition'] = f'attachment;filename="{user_file.user.username}_{user_file.tag}"'
    return response