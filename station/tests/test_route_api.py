from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status


from station.models import Station, Route
from station.serializers import RouteListSerializer, RouteDetailSerializer

ROUTE_URL = reverse("stations:route-list")


def detail_url(route_id):
    return reverse("stations:route-detail", args=[route_id])


def sample_route(**params):
    source = Station.objects.create(
        name="Central",
        latitude=50.4501,
        longitude=30.5234
    )
    destination = Station.objects.create(
        name="Terminal",
        latitude=30.5234,
        longitude=50.4501
    )

    defaults = {
        "source": source,
        "destination": destination,
        "distance": 12,
    }
    defaults.update(params)

    return Route.objects.create(**defaults)


class UnauthenticatedRouteApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_train_read_only(self):
        res = self.client.get(ROUTE_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)


class AuthenticatedTrainApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="test@test.com", password="testpassword123"
        )
        self.client.force_authenticate(self.user)
        self.route = sample_route()

        self.custom_source = Station.objects.create(
            name="East",
            latitude=5.4501,
            longitude=3.5234
        )
        self.custom_destination = Station.objects.create(
            name="Station",
            latitude=30.523,
            longitude=50.450
        )

        self.custom_route = Route.objects.create(
            source=self.custom_source,
            destination=self.custom_destination,
            distance=50
        )

    def test_route_list(self):
        routes = Route.objects.all()
        serializer = RouteListSerializer(routes, many=True)
        res = self.client.get(ROUTE_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_search_route_by_source(self):
        res = self.client.get(
            ROUTE_URL, {"search": "Central"}
        )

        serializer_sample_route = RouteListSerializer(self.route)
        serializer_custom_route = RouteListSerializer(self.custom_route)

        self.assertIn(serializer_sample_route.data, res.data)
        self.assertNotIn(serializer_custom_route.data, res.data)

    def test_search_route_by_destination(self):
        res = self.client.get(
            ROUTE_URL, {"search": "Station"}
        )

        serializer_sample_route = RouteListSerializer(self.route)
        serializer_custom_route = RouteListSerializer(self.custom_route)

        self.assertNotIn(serializer_sample_route.data, res.data)
        self.assertIn(serializer_custom_route.data, res.data)

    def test_filter_route_by_source(self):
        res = self.client.get(
            ROUTE_URL, {"source": "East"}
        )

        serializer_sample_route = RouteListSerializer(self.route)
        serializer_custom_route = RouteListSerializer(self.custom_route)

        self.assertNotIn(serializer_sample_route.data, res.data)
        self.assertIn(serializer_custom_route.data, res.data)

    def test_filter_route_by_destination(self):
        res = self.client.get(
            ROUTE_URL, {"destination": "Station"}
        )

        serializer_sample_route = RouteListSerializer(self.route)
        serializer_custom_route = RouteListSerializer(self.custom_route)

        self.assertNotIn(serializer_sample_route.data, res.data)
        self.assertIn(serializer_custom_route.data, res.data)

    def test_filter_route_by_combined_params(self):
        res = self.client.get(
            ROUTE_URL, {
                "source": "Central",
                "destination": "Terminal"
            }
        )

        serializer_sample_route = RouteListSerializer(self.route)
        serializer_custom_route = RouteListSerializer(self.custom_route)

        self.assertIn(serializer_sample_route.data, res.data)
        self.assertNotIn(serializer_custom_route.data, res.data)

    def test_retrieve_route_detail(self):
        url = detail_url(self.route.id)

        res = self.client.get(url)

        serializer = RouteDetailSerializer(self.route)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_create_route_forbidden(self):
        source = Station.objects.create(
            name="Cen",
            latitude=50.4501,
            longitude=30.5234
        )
        destination = Station.objects.create(
            name="Ter",
            latitude=30.5234,
            longitude=50.4501
        )

        payload = {
            "source": source,
            "destination": destination,
            "distance": 12,
        }

        res = self.client.post(ROUTE_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)


class AdminRouteTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="admin@test.com",
            password="testpassword123",
            is_staff=True
        )
        self.client.force_authenticate(self.user)

    def test_create_route(self):
        source = Station.objects.create(
            name="Cen",
            latitude=50.4501,
            longitude=30.5234
        )
        destination = Station.objects.create(
            name="Ter",
            latitude=30.5234,
            longitude=50.4501
        )

        payload = {
            "source": source.id,
            "destination": destination.id,
            "distance": 12,
        }

        res = self.client.post(ROUTE_URL, payload)
        route = Route.objects.get(id=res.data["id"])

        for key in payload:
            if key in ["source", "destination"]:
                self.assertEqual(payload[key], getattr(route, key).id)
            else:
                self.assertEqual(payload[key], getattr(route, key))

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
