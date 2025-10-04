from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status


from station.models import TrainType
from station.serializers import TrainTypeSerializer

TRAIN_TYPE_URL = reverse("stations:traintype-list")


def detail_url(train_type_id):
    return reverse("stations:traintype-detail", args=[train_type_id])


def sample_train_type(**params):
    defaults = {
        "name": "Passenger Express"
    }
    defaults.update(params)

    return TrainType.objects.create(**defaults)


class UnauthenticatedTrainTypeApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_train_type_read_only(self):
        res = self.client.get(TRAIN_TYPE_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)


class AuthenticatedTrainTypeApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="test@test.com", password="testpassword123"
        )
        self.client.force_authenticate(self.user)
        self.train_type = sample_train_type()

        self.custom_train_type = sample_train_type(
            name="Cargo Freight"
        )

    def test_train_type_list(self):
        train_types = TrainType.objects.all()
        serializer = TrainTypeSerializer(train_types, many=True)
        res = self.client.get(TRAIN_TYPE_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_search_train_type_by_name(self):
        res = self.client.get(
            TRAIN_TYPE_URL, {"search": "Passenger Express"}
        )

        serializer_sample_train_type = TrainTypeSerializer(self.train_type)
        serializer_custom_train_type = TrainTypeSerializer(
            self.custom_train_type
        )

        self.assertIn(serializer_sample_train_type.data, res.data)
        self.assertNotIn(serializer_custom_train_type.data, res.data)

    def test_retrieve_train_type_detail(self):
        url = detail_url(self.train_type.id)

        res = self.client.get(url)

        serializer = TrainTypeSerializer(self.train_type)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_create_train_type_forbidden(self):
        payload = {
            "name": "Passenger"
        }

        res = self.client.post(TRAIN_TYPE_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)


class AdminTrainTypeTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="admin@test.com",
            password="testpassword123",
            is_staff=True
        )
        self.client.force_authenticate(self.user)

    def test_create_train_type(self):
        payload = {
            "name": "Passenger"
        }

        res = self.client.post(TRAIN_TYPE_URL, payload)
        train_type = TrainType.objects.get(id=res.data["id"])

        for key in payload:
            self.assertEqual(payload[key], getattr(train_type, key))

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
