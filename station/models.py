from django.conf import settings
from django.db import models
from django.db.models import UniqueConstraint
from rest_framework.exceptions import ValidationError


class TrainType(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self) -> str:
        return self.name


class Train(models.Model):
    name = models.CharField(max_length=255)
    cargo_num = models.PositiveIntegerField()
    places_in_cargo = models.PositiveIntegerField()
    train_type = models.ForeignKey(
        TrainType,
        on_delete=models.CASCADE,
        related_name="trains"
    )

    def __str__(self) -> str:
        return f"{self.name} ({self.train_type})"


class Station(models.Model):
    name = models.CharField(max_length=255, unique=True)
    latitude = models.FloatField()
    longitude = models.FloatField()

    def __str__(self) -> str:
        return self.name


class Route(models.Model):
    source = models.ForeignKey(
        Station,
        on_delete=models.CASCADE,
        related_name="departures"
    )
    destination = models.ForeignKey(
        Station,
        on_delete=models.CASCADE,
        related_name="arrivals"
    )
    distance = models.PositiveIntegerField()

    def __str__(self) -> str:
        return f"{self.source} - {self.destination}"

    @staticmethod
    def validate_route(source, destination, error_to_raise):
        if source == destination:
            raise error_to_raise({
                "destination": "Source and destination "
                               "stations must be different"
            })

    def clean(self):
        Route.validate_route(self.source, self.destination, ValidationError)

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)


class Crew(models.Model):
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)

    def __str__(self) -> str:
        return f"{self.first_name} {self.last_name}"


class Journey(models.Model):
    route = models.ForeignKey(
        Route,
        on_delete=models.CASCADE,
        related_name="journeys"
    )
    train = models.ForeignKey(
        Train,
        on_delete=models.CASCADE,
        related_name="journeys"
    )
    departure_time = models.DateTimeField()
    arrival_time = models.DateTimeField()
    crew = models.ManyToManyField(
        Crew,
        related_name="journeys",
        blank=True
    )

    @staticmethod
    def validate_date(departure_time, arrival_time, error_to_raise):
        if arrival_time <= departure_time:
            raise error_to_raise({
                 "arrival_time": "Arrival time must "
                                 "be after departure time"
            })

    def clean(self):
        Journey.validate_date(
            self.departure_time,
            self.arrival_time,
            ValidationError
        )

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"Journey {self.id}: {self.route} at {self.departure_time}"


class Order(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="orders"
    )

    class Meta:
        ordering = ("-created_at", )

    def __str__(self) -> str:
        return f"Order {self.id} by {self.user}"


class Ticket(models.Model):
    cargo = models.PositiveIntegerField()
    seat = models.PositiveIntegerField()
    journey = models.ForeignKey(
        Journey,
        on_delete=models.CASCADE,
        related_name="tickets"
    )
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="tickets"
    )

    class Meta:
        constraints = [
            UniqueConstraint(
                fields=["cargo", "seat", "journey"],
                name="unique_ticket_cargo_seat_journey"
            )
        ]
        ordering = ("journey", "cargo", "seat")

    @staticmethod
    def validate_seat(seat: int, num_seats: int, error_to_raise):
        if not (1 <= seat <= num_seats):
            raise error_to_raise({
                "seat": f"seat must be in range [1, {num_seats}], not {seat}"
            })

    def clean(self):
        Ticket.validate_seat(
            self.seat,
            self.journey.train.places_in_cargo,
            ValidationError
        )

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self) -> str:
        return (f"Ticket {self.id}: "
                f"seat {self.cargo}-{self.seat} on {self.journey}")
