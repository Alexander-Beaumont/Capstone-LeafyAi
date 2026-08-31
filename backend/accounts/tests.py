from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.test import APITestCase


class RegisterUserTests(APITestCase):

    def test_register_user(self):
        data = {
            "username": "testuser",
            "password": "TestPassword123!"
        }

        response = self.client.post(
            "/api/auth/register/",
            data,
            format="json"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED
        )

        self.assertTrue(
            User.objects.filter(username="testuser").exists()
        )
    def test_register_user_password_is_hashed(self):
        data = {
            "username": "testuser",
            "password": "TestPassword123!"
        }

        self.client.post(
            "/api/auth/register/",
            data,
            format="json"
        )

        user = User.objects.get(username="testuser")

        self.assertTrue(
            user.check_password("TestPassword123!")
        )

        self.assertNotEqual(
            user.password,
            "TestPassword123!"
        )
    def test_duplicate_username_rejected(self):
        User.objects.create_user(
            username="testuser",
            password="TestPassword123!"
        )

        data = {
            "username": "testuser",
            "password": "AnotherPassword123!"
        }

        response = self.client.post(
            "/api/auth/register/",
            data,
            format="json"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST
        )
    def test_password_required(self):
        data = {
            "username": "testuser",
        }

        response = self.client.post(
            "/api/auth/register/",
            data,
            format="json"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST
        )


# Create your tests here.
