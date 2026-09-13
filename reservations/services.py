from django.db import transaction
from django.utils import timezone

from accounts.models import User
from food.models import FoodListing
from notifications.models import Notification

from .models import Reservation


class ReservationServiceError(Exception):
    def __init__(self, message, code="reservation_error"):
        super().__init__(message)
        self.message = message
        self.code = code


def create_reservation(*, customer, listing_id, quantity):
    if not customer or not customer.is_authenticated or customer.role != User.Role.CUSTOMER:
        raise ReservationServiceError("Only customer accounts can reserve food.", "invalid_role")
    try:
        quantity = int(quantity)
    except (TypeError, ValueError) as exc:
        raise ReservationServiceError("Choose a valid quantity.", "invalid_quantity") from exc
    if quantity < 1:
        raise ReservationServiceError("Choose at least one portion.", "invalid_quantity")

    with transaction.atomic():
        try:
            listing = FoodListing.objects.select_for_update().select_related("restaurant").get(pk=listing_id)
        except FoodListing.DoesNotExist as exc:
            raise ReservationServiceError("This food listing is no longer available.", "not_found") from exc

        listing.refresh_status()
        if listing.status == FoodListing.Status.EXPIRED or listing.is_expired():
            if listing.status != FoodListing.Status.EXPIRED:
                listing.status = FoodListing.Status.EXPIRED
                listing.save(update_fields=["status", "updated_at"])
            raise ReservationServiceError("This food listing has expired.", "expired")
        if listing.status == FoodListing.Status.SOLD_OUT or listing.quantity < 1:
            raise ReservationServiceError("This food listing is sold out.", "sold_out")
        if quantity > listing.quantity:
            raise ReservationServiceError(
                f"Only {listing.quantity} portion(s) remain available.",
                "insufficient_quantity",
            )

        total_price = listing.discounted_price * quantity
        reservation = Reservation.objects.create(
            customer=customer,
            food_listing=listing,
            quantity=quantity,
            total_price=total_price,
        )
        listing.quantity -= quantity
        if listing.quantity == 0:
            listing.status = FoodListing.Status.SOLD_OUT
        listing.save(update_fields=["quantity", "status", "updated_at"])
        Notification.objects.create(
            customer=customer,
            title="Reservation confirmed",
            message=f"Your {listing.name} reservation is confirmed for pay-at-collection.",
            notification_type=Notification.Type.RESERVATION,
        )
        return reservation


def cancel_reservation(*, reservation, actor):
    with transaction.atomic():
        locked = Reservation.objects.select_for_update().select_related("food_listing").get(pk=reservation.pk)
        if locked.customer_id != actor.id:
            raise ReservationServiceError("You can only cancel your own reservations.", "forbidden")
        if locked.status != Reservation.Status.RESERVED:
            raise ReservationServiceError("This reservation can no longer be cancelled.", "invalid_status")

        listing = FoodListing.objects.select_for_update().get(pk=locked.food_listing_id)
        if listing.is_expired():
            locked.status = Reservation.Status.EXPIRED
            locked.save(update_fields=["status", "updated_at"])
            raise ReservationServiceError("Expired reservations cannot be cancelled.", "expired")

        listing.quantity += locked.quantity
        if listing.status == FoodListing.Status.SOLD_OUT:
            listing.status = FoodListing.Status.ACTIVE
        listing.save(update_fields=["quantity", "status", "updated_at"])
        locked.status = Reservation.Status.CANCELLED
        locked.cancelled_at = timezone.now()
        locked.save(update_fields=["status", "cancelled_at", "updated_at"])
        Notification.objects.create(
            customer=locked.customer,
            title="Reservation cancelled",
            message=f"Your {listing.name} reservation has been cancelled.",
            notification_type=Notification.Type.STATUS,
        )
        return locked


def mark_collected(*, reservation, actor):
    with transaction.atomic():
        locked = Reservation.objects.select_for_update().select_related("food_listing__restaurant").get(pk=reservation.pk)
        if locked.food_listing.restaurant.owner_id != actor.id:
            raise ReservationServiceError("You can only update reservations for your restaurant.", "forbidden")
        if locked.status != Reservation.Status.RESERVED:
            raise ReservationServiceError("Only reserved bookings can be marked collected.", "invalid_status")
        locked.mark_collected()
        locked.save(update_fields=["status", "collected_at", "updated_at"])
        Notification.objects.create(
            customer=locked.customer,
            title="Meal collected",
            message=f"Your {locked.food_listing.name} meal has been marked as collected.",
            notification_type=Notification.Type.STATUS,
        )
        return locked
