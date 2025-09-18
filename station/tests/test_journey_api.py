from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils.dateparse import parse_datetime
from rest_framework.test import APIClient
from rest_framework import status


from station.models import (
    Station,
    Route,
    TrainType,
    Train,
    Crew,
    Journey
)
from station.serializers import (
    JourneyListSerializer,
    JourneyDetailSerializer
)

JOURNEY_URL = reverse("stations:journey-list")


def detail_url(journey_id):
    return reverse("stations:journey-detail", args=[journey_id])


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


def sample_crew(**params):
    defaults = {
        "first_name": "Nick",
        "last_name": "Fury",
    }
    defaults.update(params)

    return Crew.objects.create(**defaults)


def sample_journey(**params):
    train = params.pop('train', None)
    if train is None:
        train = sample_train()

    route = params.pop('route', None)
    if route is None:
        route = sample_route()

    defaults = {
        "train": train,
        "route": route,
        "departure_time": "2025-09-02 14:00:00",
        "arrival_time": "2025-09-03 14:00:00",
    }
    defaults.update(params)

    return Journey.objects.create(**defaults)


class UnauthenticatedJourneyApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_journey_read_only(self):
        res = self.client.get(JOURNEY_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)


class AuthenticatedJourneyApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="test@test.com", password="testpassword123"
        )
        self.client.force_authenticate(self.user)
        self.journey = sample_journey()
        self.crew = sample_crew()
        self.journey.crew.add(self.crew)

        self.train_type = TrainType.objects.create(name="Cargo Freight")
        self.custom_train = sample_train(
            name="FreightMaster 2000",
            cargo_num=20,
            places_in_cargo=50,
            train_type=self.train_type
        )
        self.source_station = Station.objects.create(
            name="East Terminal",
            latitude=50.45,
            longitude=30.52
        )
        self.destination_station = Station.objects.create(
            name="West Terminal",
            latitude=30.52,
            longitude=50.45
        )
        self.route = Route.objects.create(
                source=self.source_station,
                destination=self.destination_station,
                distance=50
            )
        self.custom_journey = Journey.objects.create(
            route=self.route,
            train=self.custom_train,
            departure_time="2025-09-05:00:00",
            arrival_time="2025-09-06:00:00"
        )
        custom_crew = sample_crew(first_name="Tony", last_name="Stark")
        self.custom_journey.crew.add(custom_crew)

    def test_journey_list(self):
        journeys = Journey.objects.all()
        serializer = JourneyListSerializer(journeys, many=True)
        res = self.client.get(JOURNEY_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        for r, s in zip(res.data, serializer.data):
            r.pop('tickets_available', None)
            self.assertEqual(r, s)

    def test_search_journey_by_train_name(self):
        res = self.client.get(
            JOURNEY_URL, {"search": "InterCity 101"}
        )

        serializer_sample_journey = JourneyListSerializer(self.journey)
        serializer_custom_journey = JourneyListSerializer(self.custom_journey)

        res_data = [dict(item) for item in res.data]
        for item in res_data:
            item.pop("tickets_available", None)

        self.assertIn(serializer_sample_journey.data, res_data)
        self.assertNotIn(serializer_custom_journey.data, res_data)

    def test_search_journey_by_route_source(self):
        res = self.client.get(
            JOURNEY_URL, {"search": "Central"}
        )

        serializer_sample_journey = JourneyListSerializer(self.journey)
        serializer_custom_journey = JourneyListSerializer(self.custom_journey)

        res_data = [dict(item) for item in res.data]
        for item in res_data:
            item.pop("tickets_available", None)

        self.assertIn(serializer_sample_journey.data, res_data)
        self.assertNotIn(serializer_custom_journey.data, res_data)

    def test_search_journey_by_route_destination(self):
        res = self.client.get(
            JOURNEY_URL, {"search": "West Terminal"}
        )

        serializer_sample_journey = JourneyListSerializer(self.journey)
        serializer_custom_journey = JourneyListSerializer(self.custom_journey)

        res_data = [dict(item) for item in res.data]
        for item in res_data:
            item.pop("tickets_available", None)

        self.assertNotIn(serializer_sample_journey.data, res_data)
        self.assertIn(serializer_custom_journey.data, res_data)

    def test_filter_journey_by_route_source(self):
        res = self.client.get(
            JOURNEY_URL, {"source": "Central"}
        )

        serializer_sample_journey = JourneyListSerializer(self.journey)
        serializer_custom_journey = JourneyListSerializer(self.custom_journey)

        res_data = [dict(item) for item in res.data]
        for item in res_data:
            item.pop("tickets_available", None)

        self.assertIn(serializer_sample_journey.data, res_data)
        self.assertNotIn(serializer_custom_journey.data, res_data)

    def test_filter_journey_by_route_destination(self):
        res = self.client.get(
            JOURNEY_URL, {"destination": "West Terminal"}
        )

        serializer_sample_journey = JourneyListSerializer(self.journey)
        serializer_custom_journey = JourneyListSerializer(self.custom_journey)

        res_data = [dict(item) for item in res.data]
        for item in res_data:
            item.pop("tickets_available", None)

        self.assertNotIn(serializer_sample_journey.data, res_data)
        self.assertIn(serializer_custom_journey.data, res_data)

    def test_filter_journey_by_train_type(self):
        res = self.client.get(
            JOURNEY_URL, {"train_type": "Cargo Freight"}
        )

        serializer_sample_journey = JourneyListSerializer(self.journey)
        serializer_custom_journey = JourneyListSerializer(self.custom_journey)

        res_data = [dict(item) for item in res.data]
        for item in res_data:
            item.pop("tickets_available", None)

        self.assertNotIn(serializer_sample_journey.data, res_data)
        self.assertIn(serializer_custom_journey.data, res_data)

    def test_filter_journey_by_departure_before(self):
        res = self.client.get(
            JOURNEY_URL, {"departure_before": "2025-09-03 20:00:00"}
        )

        serializer_sample_journey = JourneyListSerializer(self.journey)
        serializer_custom_journey = JourneyListSerializer(self.custom_journey)

        res_data = [dict(item) for item in res.data]
        for item in res_data:
            item.pop("tickets_available", None)

        self.assertIn(serializer_sample_journey.data, res_data)
        self.assertNotIn(serializer_custom_journey.data, res_data)

    def test_filter_journey_by_departure_after(self):
        res = self.client.get(
            JOURNEY_URL, {"departure_after": "2025-09-02 20:00:00"}
        )

        serializer_sample_journey = JourneyListSerializer(self.journey)
        serializer_custom_journey = JourneyListSerializer(self.custom_journey)

        res_data = [dict(item) for item in res.data]
        for item in res_data:
            item.pop("tickets_available", None)

        self.assertNotIn(serializer_sample_journey.data, res_data)
        self.assertIn(serializer_custom_journey.data, res_data)

    def test_filter_journey_by_combined_params(self):
        res = self.client.get(
            JOURNEY_URL, {
                "source": "Central",
                "destination": "Terminal",
                "departure_before": "2025-09-03 20:00:00",
                "departure_after": "2025-09-01 20:00:00"
            }
        )

        serializer_sample_journey = JourneyListSerializer(self.journey)
        serializer_custom_journey = JourneyListSerializer(self.custom_journey)

        res_data = [dict(item) for item in res.data]
        for item in res_data:
            item.pop("tickets_available", None)

        self.assertIn(serializer_sample_journey.data, res_data)
        self.assertNotIn(serializer_custom_journey.data, res_data)

    def test_retrieve_journey_detail(self):
        url = detail_url(self.journey.id)

        res = self.client.get(url)

        serializer = JourneyDetailSerializer(self.journey)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_create_journey_forbidden(self):
        train_type = TrainType.objects.create(name="Cargo")
        custom_train = sample_train(
            name="FreightMaster",
            cargo_num=20,
            places_in_cargo=50,
            train_type=train_type
        )
        source_station = Station.objects.create(
            name="East",
            latitude=50.45,
            longitude=30.52
        )
        destination_station = Station.objects.create(
            name="West",
            latitude=30.52,
            longitude=50.45
        )
        route = Route.objects.create(
                source=source_station,
                destination=destination_station,
                distance=50
            )

        payload = {
            "route": route,
            "train": custom_train,
            "departure_time": "2025-09-05:00:00",
            "arrival_time": "2025-09-06:00:00"
        }

        res = self.client.post(JOURNEY_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)


class AdminJourneyTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="admin@test.com",
            password="testpassword123",
            is_staff=True
        )
        self.client.force_authenticate(self.user)

    def test_create_journey(self):
        train_type = TrainType.objects.create(name="Cargo")
        custom_train = sample_train(
            name="FreightMaster",
            cargo_num=20,
            places_in_cargo=50,
            train_type=train_type
        )
        source_station = Station.objects.create(
            name="East",
            latitude=50.45,
            longitude=30.52
        )
        destination_station = Station.objects.create(
            name="West",
            latitude=30.52,
            longitude=50.45
        )
        route = Route.objects.create(
                source=source_station,
                destination=destination_station,
                distance=50
            )

        payload = {
            "route": route.id,
            "train": custom_train.id,
            "departure_time": "2025-09-05T00:00:00Z",
            "arrival_time": "2025-09-06T00:00:00Z",
        }

        res = self.client.post(JOURNEY_URL, payload)
        journey = Journey.objects.get(id=res.data["id"])

        for key in payload:
            if key in ["route", "train"]:
                self.assertEqual(payload[key], getattr(journey, key).id)
            elif key in ["departure_time", "arrival_time"]:
                self.assertEqual(parse_datetime(
                    payload[key]),
                    getattr(journey, key)
                )
            else:
                self.assertEqual(payload[key], getattr(journey, key))

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
