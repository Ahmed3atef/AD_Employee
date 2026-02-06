import pytest
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.db.utils import IntegrityError
from django.utils import timezone
from .models import Job, Department, Employee
from core.models import User

@pytest.mark.django_db
class EmployeeModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password123')
        self.job = Job.objects.create(title='Developer')
        self.department = Department.objects.create(name='IT')

    def test_job_creation(self):
        self.assertEqual(self.job.title, 'Developer')
        self.assertEqual(str(self.job), 'Developer')

    def test_department_creation(self):
        self.assertEqual(self.department.name, 'IT')
        self.assertEqual(str(self.department), 'IT')

    def test_employee_creation(self):
        employee = Employee.objects.create(
            user=self.user,
            full_name_en='Test User',
            full_name_ar='تجربة',
            hire_date=timezone.now().date(),
            nid='12345678901234',
            job_title=self.job,
            department=self.department
        )
        self.assertEqual(employee.user, self.user)
        self.assertEqual(employee.full_name_en, 'Test User')
        self.assertEqual(employee.job_title, self.job)
        self.assertEqual(employee.department, self.department)
        self.assertEqual(str(employee), 'Test User - Developer - IT')

    def test_employee_nid_validator(self):
        with self.assertRaises(ValidationError):
            employee = Employee(nid='123')
            employee.full_clean()

    def test_employee_protect_job(self):
        Employee.objects.create(user=self.user, job_title=self.job, department=self.department)
        with self.assertRaises(IntegrityError):
            self.job.delete()

    def test_employee_protect_department(self):
        Employee.objects.create(user=self.user, job_title=self.job, department=self.department)
        with self.assertRaises(IntegrityError):
            self.department.delete()

    def test_employee_str_with_no_job_or_department(self):
        employee = Employee.objects.create(
            user=self.user,
            full_name_en='Test User'
        )
        self.assertEqual(str(employee), 'Test User - No Job Title - No Department')
