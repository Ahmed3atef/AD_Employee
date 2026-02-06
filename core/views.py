from django.contrib.auth import login
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from drf_spectacular.utils import extend_schema, OpenApiExample
from .serializers import LoginSerializer, LoginResponseSerializer, ErrorSerializer
import logging

logger = logging.getLogger(__name__)


class LoginView(APIView):
    """
    Authenticates users against AD and returns JWT tokens on success.
    1. Validate credentials against Active Directory
    2. Create or update user in local database
    3. Generate JWT access and refresh tokens
    4. Return tokens and user information
    """
    
    permission_classes = []
    authentication_classes = []  
    
    @extend_schema(
        summary="Login with Active Directory credentials",
        description="""
        Authenticate a user against Active Directory and return JWT access/refresh tokens.
        
        """,
        request=LoginSerializer,
        responses={
            200: LoginResponseSerializer,
            400: ErrorSerializer,
            401: ErrorSerializer,
            500: ErrorSerializer,
        },
        examples=[
            OpenApiExample(
                'Successful Login',
                summary='Successful AD authentication',
                description='Returns JWT tokens and user information',
                value={
                    'access': 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...',
                    'refresh': 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...',
                    'user': {
                        'id': 1,
                        'username': 'admin@eissa.local',
                        'is_staff': True,
                        'is_superuser': True,
                        'date_joined': '2026-02-06T12:00:00Z'
                    }
                },
                response_only=True,
                status_codes=['200'],
            ),
            OpenApiExample(
                'Invalid Credentials',
                summary='Authentication failed',
                description='AD authentication rejected the credentials',
                value={
                    'error': 'Invalid credentials',
                    'detail': 'Active Directory authentication failed. Please check your username and password.'
                },
                response_only=True,
                status_codes=['401'],
            ),
            OpenApiExample(
                'Login Request',
                summary='Login with AD credentials',
                description='Provide Active Directory username and password',
                value={
                    'username': 'Administrator@eissa.local',
                    'password': 'Admin@123456'
                },
                request_only=True,
            ),
        ],
        tags=['Authentication'],
    )
    def post(self, request):
        """
        Authenticate user with Active Directory and return JWT tokens
        """
        serializer = LoginSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(
                {
                    'error': 'Validation error',
                    'detail': serializer.errors
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        username = serializer.validated_data['username']
        password = serializer.validated_data['password']
        
        try:
            
            
            user = authenticate(
                request=request,
                username=username,
                password=password
            )
            
            if not user:
                logger.warning(f"Authentication failed for {username}")
                return Response(
                    {
                        'error': 'Invalid credentials',
                        'detail': 'Active Directory authentication failed. Please check your username and password.'
                    },
                    status=status.HTTP_401_UNAUTHORIZED
                )
            
            
            if not user.is_active:
                logger.warning(f"Inactive user attempted login: {username}")
                return Response(
                    {
                        'error': 'Account disabled',
                        'detail': 'Your account has been disabled. Please contact your administrator.'
                    },
                    status=status.HTTP_401_UNAUTHORIZED
                )
                
            
            login(request, user)
            
            refresh = RefreshToken.for_user(user)
            access_token = str(refresh.access_token)
            refresh_token = str(refresh)
            
            
            user_data = {
                'id': user.id,
                'username': user.username,
                'is_staff': user.is_staff,
                'is_superuser': user.is_superuser,
                'date_joined': user.date_joined.isoformat(),
            }
            
            print(f"Successful login for user: {username}")
            
            
            return Response(
                {
                    'access': access_token,
                    'refresh': refresh_token,
                    'user': user_data
                },
                status=status.HTTP_200_OK
            )
            
        except Exception as e:
            print(f"Login error for {username}: {str(e)}", exc_info=True)
            return Response(
                {
                    'error': 'Server error',
                    'detail': 'An unexpected error occurred during authentication. Please try again later.'
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )