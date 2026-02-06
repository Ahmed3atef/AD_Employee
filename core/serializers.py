from rest_framework import serializers
from django.conf import settings


class LoginSerializer(serializers.Serializer):
    """Serializer for login request"""
    username = serializers.CharField(
        max_length=255,
        required=True,
        help_text="Active Directory username (e.g., admin@eissa.local or admin)"
    )
    password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'},
        help_text="Active Directory password"
    )
    
    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')
        
        if not username or not password:
            raise serializers.ValidationError("Username and password are required")
        
        return attrs


class UserSerializer(serializers.Serializer):
    """Serializer for user information in login response"""
    id = serializers.IntegerField(read_only=True, help_text="User ID")
    username = serializers.CharField(read_only=True, help_text="Username")
    is_staff = serializers.BooleanField(read_only=True, help_text="Staff status")
    is_superuser = serializers.BooleanField(read_only=True, help_text="Superuser status")
    date_joined = serializers.DateTimeField(read_only=True, help_text="Date user was created")


class LoginResponseSerializer(serializers.Serializer):
    """Serializer for successful login response"""
    access = serializers.CharField(
        read_only=True,
        help_text="JWT access token (expires in 5 minutes)"
    )
    refresh = serializers.CharField(
        read_only=True,
        help_text="JWT refresh token (expires in 1 day)"
    )
    user = UserSerializer(
        read_only=True,
        help_text="Authenticated user information"
    )


class ErrorSerializer(serializers.Serializer):
    """Serializer for error responses"""
    error = serializers.CharField(
        read_only=True,
        help_text="Error type/category"
    )
    detail = serializers.CharField(
        read_only=True,
        help_text="Detailed error message"
    )