from django.urls import path
from employee.views import EmployeeProfileView

urlpatterns = [
    path('profile/', EmployeeProfileView.as_view(), name='employee_profile'),
]