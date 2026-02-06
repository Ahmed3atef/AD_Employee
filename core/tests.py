
import pytest
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.db.utils import IntegrityError
from .models import User

@pytest.mark.django_db
class UserManagerTests(TestCase):
    def test_create_user(self):
        user = User.objects.create_user(username='testuser', password='password123')
        self.assertEqual(user.username, 'testuser')
        self.assertTrue(user.check_password('password123'))
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.assertTrue(user.is_active)

    def test_create_user_no_password(self):
        user = User.objects.create_user(username='testuser')
        self.assertEqual(user.username, 'testuser')
        self.assertFalse(user.has_usable_password())
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.assertTrue(user.is_active)

    def test_create_user_no_username(self):
        with self.assertRaises(ValueError):
            User.objects.create_user(username='', password='password123')

    def test_create_superuser(self):
        superuser = User.objects.create_superuser(username='superuser', password='password123')
        self.assertEqual(superuser.username, 'superuser')
        self.assertTrue(superuser.check_password('password123'))
        self.assertTrue(superuser.is_staff)
        self.assertTrue(superuser.is_superuser)
        self.assertTrue(superuser.is_active)

    def test_create_superuser_no_password(self):
        with self.assertRaises(ValueError):
            User.objects.create_superuser(username='superuser')

    def test_create_superuser_is_staff_false(self):
        with self.assertRaises(ValueError):
            User.objects.create_superuser(username='superuser', password='password123', is_staff=False)

    def test_create_superuser_is_superuser_false(self):
        with self.assertRaises(ValueError):
            User.objects.create_superuser(username='superuser', password='password123', is_superuser=False)

@pytest.mark.django_db
class UserModeTests(TestCase):
    def test_username_validator(self):
        # Valid usernames
        user1 = User(username='testuser')
        user1.full_clean()
        user2 = User(username='test.user')
        user2.full_clean()
        user3 = User(username='test_user')
        user3.full_clean()
        user4 = User(username='test-user')
        user4.full_clean()
        user5 = User(username='testuser@domain.com')
        user5.full_clean()
        
        # Invalid usernames
        with self.assertRaises(ValidationError):
            user = User(username='test user')
            user.full_clean()
        
        with self.assertRaises(ValidationError):
            user = User(username='testuser@')
            user.full_clean()
            
        with self.assertRaises(ValidationError):
            user = User(username='@domain.com')
            user.full_clean()
            
        with self.assertRaises(ValidationError):
            user = User(username='testuser@.com')
            user.full_clean()

    def test_user_str(self):
        user = User(username='testuser')
        self.assertEqual(str(user), 'testuser')

    def test_username_unique(self):
        User.objects.create_user(username='testuser', password='password123')
        with self.assertRaises(IntegrityError):
            User.objects.create_user(username='testuser', password='password123')
            
    def test_user_fields(self):
        self.assertFalse(hasattr(User, 'first_name'))
        self.assertFalse(hasattr(User, 'last_name'))
        self.assertFalse(hasattr(User, 'email'))

