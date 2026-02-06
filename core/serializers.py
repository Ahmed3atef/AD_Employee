from rest_framework import serializers
from .ad_conn import ADConnection


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)
    
    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')
        
        if not username or not password:
            raise serializers.ValidationError("Username and password are required")
        
        ad_conn = ADConnection()
        user = ad_conn(username, password)
        if not user:
            raise serializers.ValidationError("Invalid credentials")
        
        return attrs

class LoginResponseSerializer(serializers.Serializer):
    access = serializers.CharField()
    refresh = serializers.CharField()
    user = serializers.DictField()
    