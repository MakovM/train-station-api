from django.contrib import admin
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


@admin.register(TrainType)
class TrainTypeAdmin(admin.ModelAdmin):
    list_display = ["name"]


@admin.register(Train)
class TrainAdmin(admin.ModelAdmin):
    list_display = ["name", "train_type"]


@admin.register(Station)
class StationAdmin(admin.ModelAdmin):
    list_display = ["name"]


@admin.register(Route)
class RouteAdmin(admin.ModelAdmin):
    list_display = ["source", "destination"]


@admin.register(Crew)
class CrewAdmin(admin.ModelAdmin):
    list_display = ["first_name", "last_name"]


@admin.register(Journey)
class JourneyAdmin(admin.ModelAdmin):
    list_display = ["route", "departure_time", "arrival_time"]


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ["created_at", "user"]


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ["cargo", "seat", "journey"]
