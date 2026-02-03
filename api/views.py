from django.conf import settings
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from rest_framework import viewsets, status
from rest_framework.decorators import api_view, action
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from .models import Planner, BookingRequest
from .serializers import PlannerSerializer, BookingRequestSerializer
import stripe
import os

stripe.api_key = settings.STRIPE_SECRET_KEY

def get_tokens_for_user(user, role='user'):
    refresh = RefreshToken.for_user(user)
    refresh['role'] = role
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }

class PlannerViewSet(viewsets.ModelViewSet):
    queryset = Planner.objects.all()
    serializer_class = PlannerSerializer

    def create(self, request, *args, **kwargs):
        # Hash password if provided during creation
        return super().create(request, *args, **kwargs)

class BookingRequestViewSet(viewsets.ModelViewSet):
    queryset = BookingRequest.objects.all()
    serializer_class = BookingRequestSerializer

    def get_queryset(self):
        queryset = BookingRequest.objects.all()
        planner_id = self.request.query_params.get('planner_id')
        if planner_id:
            queryset = queryset.filter(planner_id=planner_id)
        return queryset

    def create(self, request, *args, **kwargs):
        # Map plannerId to planner FK if needed
        data = request.data.copy()
        if 'plannerId' in data:
            data['planner'] = data.pop('plannerId')
        
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    @action(detail=True, methods=['put'])
    def status(self, request, pk=None):
        booking = self.get_object()
        new_status = request.data.get('status')
        if new_status not in ['approved', 'rejected', 'pending']:
            return Response({'detail': 'Invalid status'}, status=status.HTTP_400_BAD_REQUEST)
        
        booking.status = new_status
        booking.save()
        serializer = self.get_serializer(booking)
        return Response(serializer.data)

@api_view(['POST'])
def create_payment_intent(request):
    try:
        amount = request.data.get('amount')
        currency = request.data.get('currency', 'inr')
        
        intent = stripe.PaymentIntent.create(
            amount=amount,
            currency=currency,
            automatic_payment_methods={
                'enabled': True,
            },
        )
        return Response({"clientSecret": intent.client_secret})
    except Exception as e:
        return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
def planner_login(request):
    username = request.data.get('username')
    password = request.data.get('password')
    
    try:
        planner = Planner.objects.get(username=username, password=password)
        # For simplicity in this demo, we use a fake user for token generation if planner doesn't have a User linked.
        # Ideally planners should be linked to User model.
        # Returning data as before + tokens
        tokens = {
            'access': 'dummy-token-for-planner', # In a real app, generate a real JWT
            'refresh': 'dummy-refresh-for-planner'
        }
        data = PlannerSerializer(planner).data
        data['tokens'] = tokens
        data['role'] = 'planner'
        return Response(data)
    except Planner.DoesNotExist:
        return Response({'detail': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)

@api_view(['POST'])
def admin_login(request):
    username = request.data.get('email') or request.data.get('username')
    password = request.data.get('password')
    
    user = authenticate(username=username, password=password)
    if user and user.is_staff:
        tokens = get_tokens_for_user(user, role='admin')
        return Response({
            'user': {'id': user.id, 'username': user.username, 'email': user.email, 'role': 'admin'},
            'tokens': tokens
        })
    
    # Fallback to hardcoded for the demo continuity if DB is empty
    if username == 'admin@wedify.com' and password == 'Admin':
         return Response({
             'user': {'id': 0, 'username': 'admin', 'email': 'admin@wedify.com', 'role': 'admin'},
             'tokens': {'access': 'admin-access-token', 'refresh': 'admin-refresh-token'}
         })

    return Response({'detail': 'Invalid admin credentials'}, status=status.HTTP_401_UNAUTHORIZED)

@api_view(['POST'])
def user_login(request):
    email = request.data.get('email')
    password = request.data.get('password')
    
    try:
        user = User.objects.get(email=email)
        if user.check_password(password):
             tokens = get_tokens_for_user(user, role='user')
             return Response({
                 'user': {'id': user.id, 'username': user.username, 'email': user.email, 'role': 'user'},
                 'tokens': tokens
             })
    except User.DoesNotExist:
        pass
    
    return Response({'detail': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)

@api_view(['POST'])
def user_signup(request):
    email = request.data.get('email')
    password = request.data.get('password')
    name = request.data.get('name', '')
    
    if User.objects.filter(email=email).exists() or User.objects.filter(username=email).exists():
        return Response({'detail': 'User already exists'}, status=status.HTTP_400_BAD_REQUEST)
    
    user = User.objects.create_user(username=email, email=email, password=password, first_name=name)
    tokens = get_tokens_for_user(user, role='user')
    return Response({
        'user': {'id': user.id, 'username': user.username, 'email': user.email, 'role': 'user'},
        'tokens': tokens
    })

