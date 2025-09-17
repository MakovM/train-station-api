from django.db.models import F, Count
from rest_framework import viewsets

from station.filters import (
    TrainFilter,
    RouteFilter,
    JourneyFilter,
    OrderFilter
)
from station.models import (
    Train,
    TrainType,
    Station,
    Route,
    Crew,
    Journey,
    Order,
)
from station.serializers import (
    TrainSerializer,
    TrainTypeSerializer,
    StationSerializer,
    RouteSerializer,
    CrewSerializer,
    JourneySerializer,
    OrderSerializer,
    TrainListSerializer,
    TrainDetailSerializer,
    RouteListSerializer,
    RouteDetailSerializer,
    JourneyListSerializer,
    JourneyDetailSerializer,
    OrderListSerializer, OrderDetailSerializer
)


class TrainTypeViewSet(viewsets.ModelViewSet):
    queryset = TrainType.objects.all()
    serializer_class = TrainTypeSerializer
    search_fields = ["name"]


class TrainViewSet(viewsets.ModelViewSet):
    queryset = Train.objects.all()
    filterset_class = TrainFilter
    search_fields = ["name"]

    def get_queryset(self):
        queryset = self.queryset
        if self.action == "list":
            queryset = queryset.select_related("train_type")
        return queryset

    def get_serializer_class(self):
        if self.action == "list":
            return TrainListSerializer
        elif self.action == "retrieve":
            return TrainDetailSerializer
        return TrainSerializer


class StationViewSet(viewsets.ModelViewSet):
    queryset = Station.objects.all()
    serializer_class = StationSerializer
    search_fields = ["name"]


class RouteViewSet(viewsets.ModelViewSet):
    queryset = Route.objects.select_related("source", "destination")
    filterset_class = RouteFilter
    search_fields = ["source__name", "destination__name"]

    def get_serializer_class(self):
        if self.action == "list":
            return RouteListSerializer
        elif self.action == "retrieve":
            return RouteDetailSerializer
        return RouteSerializer


class CrewViewSet(viewsets.ModelViewSet):
    queryset = Crew.objects.all()
    serializer_class = CrewSerializer
    search_fields = ["first_name", "last_name"]


class JourneyViewSet(viewsets.ModelViewSet):
    queryset = Journey.objects.all()
    filterset_class = JourneyFilter
    search_fields = [
        "train__name",
        "route__source__name",
        "route__destination__name"
    ]

    def get_queryset(self):
        queryset = self.queryset
        if self.action == "list":
            queryset = queryset.select_related(
                "route__source",
                "route__destination",
                "train__train_type"
            ).prefetch_related(
                "crew"
            ).annotate(
                tickets_available=(
                        F("train__cargo_num")
                        * F("train__places_in_cargo")
                        - Count("tickets")
                )
            )
        elif self.action == "retrieve":
            queryset = queryset.select_related(
                "route__source",
                "route__destination",
                "train__train_type"
            ).prefetch_related(
                "crew"
            )
        return queryset

    def get_serializer_class(self):
        if self.action == "list":
            return JourneyListSerializer
        elif self.action == "retrieve":
            return JourneyDetailSerializer
        return JourneySerializer


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    filterset_class = OrderFilter

    def get_queryset(self):
        queryset = self.queryset.filter(user=self.request.user)
        if self.action == "list":
            queryset = queryset.prefetch_related(
                "tickets__journey__train__train_type",
                "tickets__journey__crew",
                "tickets__journey__route",
            )
        elif self.action == "retrieve":
            queryset = queryset.prefetch_related(
                "tickets__journey__train__train_type",
                "tickets__journey__crew",
                "tickets__journey__route",
            )
        return queryset

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def get_serializer_class(self):
        serializer = self.serializer_class
        if self.action == "list":
            serializer = OrderListSerializer
        elif self.action == "retrieve":
            serializer = OrderDetailSerializer
        return serializer
