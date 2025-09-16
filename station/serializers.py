from rest_framework import serializers

from station.models import Train, TrainType, Station, Route, Crew, Journey, Order, Ticket


class TrainTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrainType
        fields = ("id", "name")


class TrainSerializer(serializers.ModelSerializer):
    class Meta:
        model = Train
        fields = ("id", "name", "cargo_num", "places_in_cargo", "train_type")


class TrainListSerializer(TrainSerializer):
    train_type = serializers.CharField(source="train_type.name", read_only=True)

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


class RouteListSerializer(RouteSerializer):
    source = serializers.SlugRelatedField(read_only=True, slug_field="name")
    destination = serializers.SlugRelatedField(read_only=True, slug_field="name")


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
        fields = ("id", "route", "train", "departure_time", "arrival_time", "crew")

class JourneyListSerializer(JourneySerializer):
    train = TrainListSerializer(many=False, read_only=True)
    route = RouteListSerializer(many=False, read_only=True)
    crew = serializers.StringRelatedField(many=True, read_only=True)


class JourneyDetailSerializer(JourneySerializer):
    train = TrainDetailSerializer(many=False, read_only=True)
    route = RouteDetailSerializer(many=False, read_only=True)
    crew = CrewSerializer(many=True, read_only=True)


class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ("id", "created_at", "user")


class TicketSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ticket
        fields = ("id", "cargo", "seat", "journey", "order")

