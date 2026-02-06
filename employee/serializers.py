from rest_framework import serializers
from .models import Employee, Job, Department


class JobSerializer(serializers.ModelSerializer):
    class Meta:
        model = Job
        fields = ['id', 'title']
        
class DeparmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = ['id', 'name']

class EmployeeProfileSerializer(serializers.ModelSerializer):
    
    username = serializers.CharField(source='user.username', read_only=True)
    job_title = JobSerializer(read_only=True)
    department = DeparmentSerializer(read_only=True)
    
    email = serializers.EmailField(read_only=True, required=False)
    phone = serializers.CharField(read_only=True, required=False)
    ou = serializers.CharField(read_only=True, required=False)
    display_name = serializers.CharField(read_only=True, required=False)
    distinguished_name = serializers.CharField(read_only=True, required=False)
    
    class Meta:
        model = Employee
        fields = [
            'id',
            'username',
            'full_name_en',
            'full_name_ar',
            'hire_date',
            'nid',
            'job_title',
            'department',
            # AD fields
            'email',
            'phone',
            'ou',
            'display_name',
            'distinguished_name',
        ]
        read_only_fields = ['id', 'username', 'hire_date']