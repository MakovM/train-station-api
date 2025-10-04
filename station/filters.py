import django_filters

from station.models import Train, Route, Journey, Order


class TrainFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(
        field_name="name",
        lookup_expr="icontains",
        label="Train"
    )
    train_type = django_filters.CharFilter(
        field_name="train_type__name",
        lookup_expr="icontains",
        label="Train"
    )

    class Meta:
        model = Train
        fields = ("name", "train_type")


class RouteFilter(django_filters.FilterSet):
    source = django_filters.CharFilter(
        field_name="source__name",
        lookup_expr="icontains",
        label="Source"
    )
    destination = django_filters.CharFilter(
        field_name="destination__name",
        lookup_expr="icontains",
        label="Destination"
    )

    class Meta:
        model = Route
        fields = ("source", "destination")


class JourneyFilter(django_filters.FilterSet):
    source = django_filters.CharFilter(
        field_name="route__source__name",
        lookup_expr="icontains"
    )
    destination = django_filters.CharFilter(
        field_name="route__destination__name",
        lookup_expr="icontains"
    )
    train_type = django_filters.CharFilter(
        field_name="train__train_type__name",
        lookup_expr="icontains"
    )
    departure_after = django_filters.DateTimeFilter(
        field_name="departure_time",
        lookup_expr="gte"
    )
    departure_before = django_filters.DateTimeFilter(
        field_name="departure_time",
        lookup_expr="lte"
    )

    class Meta:
        model = Journey
        fields = [
            "source",
            "destination",
            "train_type",
            "departure_after",
            "departure_before"
        ]


class OrderFilter(django_filters.FilterSet):
    created_after = django_filters.DateTimeFilter(
        field_name="created_at",
        lookup_expr="gte"
    )
    created_before = django_filters.DateTimeFilter(
        field_name="created_at",
        lookup_expr="lte"
    )

    class Meta:
        model = Order
        fields = ["created_after", "created_before"]
