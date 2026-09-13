from datetime import timedelta
from decimal import Decimal, ROUND_HALF_UP

from django.conf import settings
from django.utils import timezone

from reservations.models import Reservation
from restaurants.models import Restaurant


def _quantize(value):
    return Decimal(value).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _impact_for(reservations):
    collected = reservations.filter(status=Reservation.Status.COLLECTED).select_related("food_listing")
    meals_served = 0
    savings = Decimal("0.00")
    for reservation in collected:
        meals_served += reservation.quantity
        savings += (
            reservation.food_listing.original_price - reservation.food_listing.discounted_price
        ) * reservation.quantity
    food_saved_kg = _quantize(meals_served * Decimal(str(settings.FOOD_WEIGHT_KG)))
    co2_avoided_kg = _quantize(food_saved_kg * Decimal(str(settings.CO2_KG_PER_KG_FOOD)))
    return {
        "meals_served": meals_served,
        "food_saved_kg": food_saved_kg,
        "co2_avoided_kg": co2_avoided_kg,
        "customer_savings": _quantize(savings),
    }


def _with_common_metrics(metrics, reservations):
    current_month = timezone.localdate().replace(day=1)
    monthly = reservations.filter(status=Reservation.Status.COLLECTED, created_at__date__gte=current_month)
    metrics["reservations"] = reservations.count()
    metrics["monthly_meals"] = sum(item.quantity for item in monthly)
    return metrics


def get_platform_impact():
    reservations = Reservation.objects.all()
    metrics = _impact_for(reservations)
    metrics["restaurants"] = Restaurant.objects.filter(
        food_listings__reservations__status=Reservation.Status.COLLECTED,
    ).distinct().count()
    return _with_common_metrics(metrics, reservations)


def get_customer_impact(customer):
    reservations = Reservation.objects.filter(customer=customer)
    metrics = _impact_for(reservations)
    metrics["restaurants"] = reservations.filter(
        status=Reservation.Status.COLLECTED,
    ).values("food_listing__restaurant").distinct().count()
    return _with_common_metrics(metrics, reservations)


def get_restaurant_impact(restaurant):
    reservations = Reservation.objects.filter(food_listing__restaurant=restaurant)
    metrics = _impact_for(reservations)
    metrics["restaurants"] = 1
    return _with_common_metrics(metrics, reservations)
