from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status


from station.models import Station
from station.serializers import StationSerializer

STATION_URL = reverse("stations:station-list")


def detail_url(station_id):
    return reverse("stations:station-detail", args=[station_id])


def sample_station(**params):
    defaults = {
        "name": "Central Station",
        "latitude": 50.4501,
        "longitude": 30.5234,
    }
    defaults.update(params)

    return Station.objects.create(**defaults)


class UnauthenticatedStationApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_station_read_only(self):
        res = self.client.get(STATION_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)


class AuthenticatedStationApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="test@test.com", password="testpassword123"
        )
        self.client.force_authenticate(self.user)
        self.station = sample_station()

        self.custom_station = sample_station(
            name="West Terminal",
            latitude=50.4501,
            longitude=30.5234
        )

    def test_stations_list(self):
        stations = Station.objects.all()
        serializer = StationSerializer(stations, many=True)
        res = self.client.get(STATION_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_search_stations_by_name(self):
        res = self.client.get(
            STATION_URL, {"search": "West Terminal"}
        )

        serializer_sample_station = StationSerializer(self.station)
        serializer_custom_station = StationSerializer(self.custom_station)

        self.assertNotIn(serializer_sample_station, res.data)
        self.assertIn(serializer_custom_station.data, res.data)

    def test_retrieve_station_detail(self):
        url = detail_url(self.station.id)

        res = self.client.get(url)

        serializer = StationSerializer(self.station)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_create_station_forbidden(self):
        payload = {
            "name": "East Terminal",
            "latitude": 1.1,
            "longitude": 1.2,
        }

        res = self.client.post(STATION_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)


class AdminStationTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="admin@test.com",
            password="testpassword123",
            is_staff=True
        )
        self.client.force_authenticate(self.user)

    def test_create_station(self):
        payload = {
            "name": "East Terminal",
            "latitude": 1.1,
            "longitude": 1.2,
        }

        res = self.client.post(STATION_URL, payload)
        station = Station.objects.get(id=res.data["id"])

        for key in payload:
            self.assertEqual(payload[key], getattr(station, key))

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
