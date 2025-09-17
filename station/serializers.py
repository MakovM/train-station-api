from django.db import transaction
from rest_framework import serializers

from station.models import (
    Train,
    TrainType,
    Station,
    Route,
    Crew,
    Journey,
    Order,
    Ticket
)


class TrainTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrainType
        fields = ("id", "name")


class TrainSerializer(serializers.ModelSerializer):
    class Meta:
        model = Train
        fields = ("id", "name", "cargo_num", "places_in_cargo", "train_type")


class TrainListSerializer(TrainSerializer):
    train_type = serializers.CharField(
        source="train_type.name",
        read_only=True
    )

    class Meta(TrainSerializer.Meta):
        fields = TrainSerializer.Meta.fields + ("train_type", )


class TrainDetailSerializer(TrainSerializer):
    train_type = TrainTypeSerializer(read_only=True)

    class Meta(TrainSerializer.Meta):
        fields = TrainSerializer.Meta.fields + ("train_type", )


class StationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Station
        fields = ("id", "name", "latitude", "longitude")


class RouteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Route
        fields = ("id", "source", "destination", "distance")

    def validate(self, attrs):
        Route.validate_route(
            attrs["source"],
            attrs["destination"],
            serializers.ValidationError
        )


class RouteListSerializer(RouteSerializer):
    source = serializers.CharField(source='source.name', read_only=True)
    destination = serializers.CharField(
        source='destination.name',
        read_only=True
    )


class RouteDetailSerializer(RouteSerializer):
    source = StationSerializer(read_only=True)
    destination = StationSerializer(read_only=True)


class CrewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Crew
        fields = ("id", "first_name", "last_name")


class JourneySerializer(serializers.ModelSerializer):
    class Meta:
        model = Journey
        fields = (
            "id",
            "route",
            "train",
            "departure_time",
            "arrival_time",
            "crew"
        )

        def validate(self, attrs):
            Journey.validate_date(
                attrs["departure_time"],
                attrs["arrival_time"],
                serializers.ValidationError
            )


class JourneyListSerializer(JourneySerializer):
    train = TrainListSerializer(many=False, read_only=True)
    route = RouteListSerializer(many=False, read_only=True)
    crew = serializers.StringRelatedField(many=True, read_only=True)
    tickets_available = serializers.IntegerField(read_only=True)

    class Meta(JourneySerializer.Meta):
        fields = JourneySerializer.Meta.fields + ("tickets_available",)


class SeatSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ticket
        fields = ("cargo", "seat")


class JourneyDetailSerializer(JourneySerializer):
    train = TrainDetailSerializer(many=False, read_only=True)
    route = RouteDetailSerializer(many=False, read_only=True)
    crew = CrewSerializer(many=True, read_only=True)
    taken_seats = SeatSerializer(source="tickets", many=True, read_only=True)

    class Meta(JourneySerializer.Meta):
        fields = JourneySerializer.Meta.fields + ("taken_seats",)


class JourneyForTicketSerializer(JourneySerializer):
    route = RouteListSerializer()
    train = serializers.CharField(source="train.name")

    class Meta:
        model = Journey
        fields = (
            "route",
            "train",
            "departure_time",
            "arrival_time",
        )


class TicketSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ticket
        fields = ("id", "cargo", "seat", "journey")

    def validate(self, attrs):
        Ticket.validate_seat(
            attrs["seat"],
            attrs["journey"].train.places_in_cargo,
            serializers.ValidationError
        )


class TicketListSerializer(TicketSerializer):
    journey = JourneyForTicketSerializer(read_only=True)


class TicketDetailSerializer(TicketSerializer):
    journey = JourneyDetailSerializer(read_only=True)


class OrderSerializer(serializers.ModelSerializer):
    tickets = TicketListSerializer(
        many=True,
        read_only=False,
        allow_empty=False
    )

    class Meta:
        model = Order
        fields = ("id", "created_at", "tickets")

    def create(self, validated_data):
        with transaction.atomic():
            tickets_data = validated_data.pop("tickets")
            order = Order.objects.create(**validated_data)
            for ticket_data in tickets_data:
                Ticket.objects.create(order=order, **ticket_data)
            return order


class OrderListSerializer(OrderSerializer):
    tickets = TicketListSerializer(read_only=True, many=True)


class OrderDetailSerializer(OrderSerializer):
    tickets = TicketDetailSerializer(read_only=True, many=True)
