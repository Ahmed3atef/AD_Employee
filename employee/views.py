import re
from rest_framework.views import APIView
from rest_framework.response import Response
from django.core.cache import cache
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.conf import settings
from drf_spectacular.utils import extend_schema, OpenApiExample
from .models import Employee
from .serializers import EmployeeProfileSerializer
import logging

logger = logging.getLogger(__name__)


class EmployeeProfileView(APIView):
    
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        summary="Get employee profile",
        description="""
        Retrieves employee profile information by combining:
        """,
        responses={
            200: EmployeeProfileSerializer,
            404: {
                'type': 'object',
                'properties': {
                    'error': {'type': 'string'},
                    'detail': {'type': 'string'}
                }
            },
            500: {
                'type': 'object',
                'properties': {
                    'error': {'type': 'string'},
                    'detail': {'type': 'string'}
                }
            }
        },
        examples=[
            OpenApiExample(
                'Success Response',
                summary='Employee profile retrieved successfully',
                value={
                    'id': 1,
                    'username': 'ahmed.hassan@eissa.local',
                    'full_name_en': 'Ahmed Hassan',
                    'full_name_ar': 'أحمد حسن',
                    'hire_date': '2024-01-15',
                    'nid': '12345678901234',
                    'job_title': {
                        'id': 1,
                        'title': 'Software Engineer'
                    },
                    'department': {
                        'id': 1,
                        'name': 'IT'
                    },
                    'email': 'ahmed.hassan@eissa.local',
                    'phone': '110031',
                    'ou': 'IT',
                    'display_name': 'ahmed hassan',
                    'distinguished_name': 'CN=ahmed hassan,OU=IT,OU=New,DC=eissa,DC=local'
                },
                response_only=True,
                status_codes=['200'],
            ),
        ],
        tags=['Employee'],
    )
    def get(self, request):
        
        try:
            try:
                employee = Employee.objects.select_related(
                    'user', 'job_title', 'department'
                ).get(user=request.user)
            except Employee.DoesNotExist:
                return Response(
                    {
                        'error': 'Profile not found',
                        'detail': 'No employee profile found for this user. Please contact your administrator.'
                    },
                    status=status.HTTP_404_NOT_FOUND
                )
            
            
            ad_creds = cache.get(f'ad_creds_{request.user.id}')
            ad_username = ad_creds['username']
            ad_password = ad_creds['password']
            
            serializer = EmployeeProfileSerializer(employee)
            employee_data = serializer.data
            
            
            if ad_username and ad_password:
                try:
                    ad = settings.ACTIVE_DIR
                    
                    
                    if ad.connect_ad(ad_username, ad_password):
                        
                        clean_username = ad_username.split('@')[0]
                        
                        entries = ad.search_user_full_info(
                            clean_username,
                            attributes=['mail', 'telephoneNumber', 'displayName', 'distinguishedName']
                        )
                        
                        if entries and len(entries) > 0:
                            entry = entries[0]
                            
                            
                            def get_clean_val(attr_name):
                                val = getattr(entry, attr_name, None)
                                if not val or val == [] or str(val).strip() == "":
                                    return None
                                if isinstance(val, list):
                                    return str(val[0]).strip()
                                return str(val).strip()
                            
                            
                            employee_data['email'] = get_clean_val('mail')
                            employee_data['phone'] = get_clean_val('telephoneNumber')
                            employee_data['display_name'] = get_clean_val('displayName')
                            
                            
                            dn = get_clean_val('distinguishedName') or entry.entry_dn
                            employee_data['distinguished_name'] = dn
                            
                            ou_match = re.search(r'OU=([^,]+)', dn)
                            if ou_match:
                                employee_data['ou'] = ou_match.group(1).strip()
                            
                            logger.info(f"Successfully retrieved AD data for user: {clean_username}")
                        else:
                            logger.warning(f"User not found in AD: {clean_username}")
                    else:
                        logger.warning(f"Failed to connect to AD for user: {ad_username}")
                        
                except Exception as ad_error:
                    
                    logger.error(f"Error fetching AD data: {str(ad_error)}")
            else:
                logger.warning("AD credentials not found in session")
            
            return Response(employee_data, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error retrieving employee profile: {str(e)}", exc_info=True)
            return Response(
                {
                    'error': 'Server error',
                    'detail': 'An unexpected error occurred while retrieving your profile.'
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )