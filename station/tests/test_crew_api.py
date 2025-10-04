from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status


from station.models import Crew
from station.serializers import CrewSerializer

CREW_URL = reverse("stations:crew-list")


def detail_url(crew_id):
    return reverse("stations:crew-detail", args=[crew_id])


def sample_crew(**params):
    defaults = {
        "first_name": "Nick",
        "last_name": "Fury",
    }
    defaults.update(params)

    return Crew.objects.create(**defaults)


class UnauthenticatedCrewApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_crew_read_only(self):
        res = self.client.get(CREW_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)


class AuthenticatedCrewApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="test@test.com", password="testpassword123"
        )
        self.client.force_authenticate(self.user)
        self.crew = sample_crew()

        self.custom_crew = sample_crew(
            first_name="Bob",
            last_name="Marley"
        )

    def test_crews_list(self):
        crews = Crew.objects.all()
        serializer = CrewSerializer(crews, many=True)
        res = self.client.get(CREW_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_search_crews_by_first_name(self):
        res = self.client.get(
            CREW_URL, {"search": "Nick"}
        )

        serializer_sample_crew = CrewSerializer(self.crew)
        serializer_custom_crew = CrewSerializer(self.custom_crew)

        self.assertIn(serializer_sample_crew.data, res.data)
        self.assertNotIn(serializer_custom_crew.data, res.data)

    def test_search_crews_by_last_name(self):
        res = self.client.get(
            CREW_URL, {"search": "Fury"}
        )

        serializer_sample_crew = CrewSerializer(self.crew)
        serializer_custom_crew = CrewSerializer(self.custom_crew)

        self.assertIn(serializer_sample_crew.data, res.data)
        self.assertNotIn(serializer_custom_crew.data, res.data)

    def test_retrieve_crew_detail(self):
        url = detail_url(self.crew.id)

        res = self.client.get(url)

        serializer = CrewSerializer(self.crew)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_create_crew_forbidden(self):
        payload = {
            "first_name": "Bob",
            "last_name": "Fury",
        }

        res = self.client.post(CREW_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)


class AdminCrewTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="admin@test.com",
            password="testpassword123",
            is_staff=True
        )
        self.client.force_authenticate(self.user)

    def test_create_crew(self):
        payload = {
            "first_name": "Bob",
            "last_name": "Fury",
        }

        res = self.client.post(CREW_URL, payload)
        crew = Crew.objects.get(id=res.data["id"])

        for key in payload:
            self.assertEqual(payload[key], getattr(crew, key))

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
