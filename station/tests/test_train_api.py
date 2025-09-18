from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status


from station.models import TrainType, Train
from station.serializers import TrainListSerializer, TrainDetailSerializer

TRAIN_URL = reverse("stations:train-list")


def detail_url(train_id):
    return reverse("stations:train-detail", args=[train_id])


def sample_train(**params):
    train_type = TrainType.objects.create(name="Passenger Express")
    defaults = {
        "name": "InterCity 101",
        "cargo_num": 15,
        "places_in_cargo": 40,
        "train_type": train_type
    }
    defaults.update(params)

    return Train.objects.create(**defaults)


class UnauthenticatedTrainApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_train_read_only(self):
        res = self.client.get(TRAIN_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)


class AuthenticatedTrainApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="test@test.com", password="testpassword123"
        )
        self.client.force_authenticate(self.user)
        self.train = sample_train()

        self.train_type = TrainType.objects.create(name="Cargo Freight")
        self.custom_train = sample_train(
            name="FreightMaster 2000",
            cargo_num=20,
            places_in_cargo=50,
            train_type=self.train_type
        )

    def test_trains_list(self):
        trains = Train.objects.all()
        serializer = TrainListSerializer(trains, many=True)
        res = self.client.get(TRAIN_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_search_trains_by_name(self):
        res = self.client.get(
            TRAIN_URL, {"search": "InterCity 101"}
        )

        serializer_sample_train = TrainListSerializer(self.train)
        serializer_custom_train = TrainListSerializer(self.custom_train)

        self.assertIn(serializer_sample_train.data, res.data)
        self.assertNotIn(serializer_custom_train.data, res.data)

    def test_filter_trains_by_name(self):
        res = self.client.get(
            TRAIN_URL, {"name": "FreightMaster 2000"}
        )

        serializer_sample_train = TrainListSerializer(self.train)
        serializer_custom_train = TrainListSerializer(self.custom_train)

        self.assertNotIn(serializer_sample_train, res.data)
        self.assertIn(serializer_custom_train.data, res.data)

    def test_filter_trains_by_type(self):
        res = self.client.get(
            TRAIN_URL, {"train_type": "Passenger Express"}
        )

        serializer_sample_train = TrainListSerializer(self.train)
        serializer_custom_train = TrainListSerializer(self.custom_train)

        self.assertIn(serializer_sample_train.data, res.data)
        self.assertNotIn(serializer_custom_train, res.data)

    def test_filter_trains_by_combined_params(self):
        res = self.client.get(
            TRAIN_URL,
            {
                "name": "InterCity 101",
                "train_type": "Passenger Express",
            },
        )

        serializer_sample_train = TrainListSerializer(self.train)
        serializer_custom_train = TrainListSerializer(self.custom_train)

        self.assertIn(serializer_sample_train.data, res.data)
        self.assertNotIn(serializer_custom_train, res.data)

    def test_retrieve_train_detail(self):
        url = detail_url(self.train.id)

        res = self.client.get(url)

        serializer = TrainDetailSerializer(self.train)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_create_train_forbidden(self):
        payload = {
            "name": "InterCity 102",
            "cargo_num": 15,
            "places_in_cargo": 40,
            "train_type": self.train_type.id
        }

        res = self.client.post(TRAIN_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)


class AdminTrainTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="admin@test.com",
            password="testpassword123",
            is_staff=True
        )
        self.client.force_authenticate(self.user)
        self.train_type = TrainType.objects.create(name="Cargo Freight")

    def test_create_train(self):
        payload = {
            "name": "InterCity 102",
            "cargo_num": 15,
            "places_in_cargo": 40,
            "train_type": self.train_type.id
        }

        res = self.client.post(TRAIN_URL, payload)
        train = Train.objects.get(id=res.data["id"])

        for key in payload:
            if key == "train_type":
                self.assertEqual(payload[key], getattr(train, key).id)
            else:
                self.assertEqual(payload[key], getattr(train, key))

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
