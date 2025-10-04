from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status


JOURNEY_URL = reverse("stations:journey-list")


class JwtAuthFlowTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="jwtuser@test.com",
            password="testpass123",
            is_staff=True
        )

    def test_jwt_token_authentication(self):
        res = self.client.post(
            reverse("user:token_obtain_pair"),
            {"email": "jwtuser@test.com", "password": "testpass123"},
            format="json"
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn("access", res.data)

        token = res.data["access"]

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        res = self.client.get(JOURNEY_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
