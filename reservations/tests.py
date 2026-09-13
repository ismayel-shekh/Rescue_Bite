from datetime import timedelta
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import User
from food.models import FoodListing
from restaurants.models import Restaurant

from .models import Reservation
from .services import ReservationServiceError, cancel_reservation, create_reservation, mark_collected


class ReservationServiceTests(TestCase):
    def setUp(self):
        self.customer = User.objects.create_user(
            email="customer@example.com",
            password="StrongPass123!",
            name="Customer",
            role=User.Role.CUSTOMER,
        )
        self.owner = User.objects.create_user(
            email="owner@example.com",
            password="StrongPass123!",
            name="Owner",
            role=User.Role.RESTAURANT_OWNER,
        )
        self.other_owner = User.objects.create_user(
            email="other@example.com",
            password="StrongPass123!",
            name="Other Owner",
            role=User.Role.RESTAURANT_OWNER,
        )
        self.restaurant = Restaurant.objects.create(owner=self.owner, name="Campus Bites", address="AIU")
        self.listing = self.make_listing()

    def make_listing(self, **overrides):
        values = {
            "restaurant": self.restaurant,
            "name": "Chicken Biryani",
            "original_price": Decimal("10.00"),
            "discount_percentage": 50,
            "quantity": 5,
            "pickup_date": timezone.localdate(),
            "pickup_start": "21:00",
            "pickup_end": "23:00",
        }
        values.update(overrides)
        return FoodListing.objects.create(**values)

    def test_create_reservation_reduces_inventory_and_uses_server_price(self):
        reservation = create_reservation(customer=self.customer, listing_id=self.listing.pk, quantity=2)
        self.listing.refresh_from_db()
        self.assertEqual(reservation.total_price, Decimal("10.00"))
        self.assertEqual(self.listing.quantity, 3)
        self.assertTrue(reservation.reservation_code.startswith("RB-"))

    def test_create_reservation_rejects_more_than_available(self):
        with self.assertRaises(ReservationServiceError):
            create_reservation(customer=self.customer, listing_id=self.listing.pk, quantity=6)

    def test_create_reservation_rejects_expired_listing(self):
        expired_listing = self.make_listing(pickup_date=timezone.localdate() - timedelta(days=1))
        with self.assertRaises(ReservationServiceError):
            create_reservation(customer=self.customer, listing_id=expired_listing.pk, quantity=1)

    def test_create_reservation_rejects_non_customer(self):
        with self.assertRaises(ReservationServiceError):
            create_reservation(customer=self.owner, listing_id=self.listing.pk, quantity=1)

    def test_reserving_final_portion_marks_listing_sold_out(self):
        listing = self.make_listing(quantity=1)
        create_reservation(customer=self.customer, listing_id=listing.pk, quantity=1)
        listing.refresh_from_db()
        self.assertEqual(listing.status, FoodListing.Status.SOLD_OUT)

    def test_customer_can_cancel_reserved_booking_and_restore_inventory(self):
        reservation = create_reservation(customer=self.customer, listing_id=self.listing.pk, quantity=2)
        cancel_reservation(reservation=reservation, actor=self.customer)
        reservation.refresh_from_db()
        self.listing.refresh_from_db()
        self.assertEqual(reservation.status, Reservation.Status.CANCELLED)
        self.assertEqual(self.listing.quantity, 5)

    def test_owner_can_mark_only_own_reservation_collected(self):
        reservation = create_reservation(customer=self.customer, listing_id=self.listing.pk, quantity=1)
        mark_collected(reservation=reservation, actor=self.owner)
        reservation.refresh_from_db()
        self.assertEqual(reservation.status, Reservation.Status.COLLECTED)

        other_restaurant = Restaurant.objects.create(owner=self.other_owner, name="Other", address="AIU")
        other_listing = self.make_listing(restaurant=other_restaurant)
        other_reservation = create_reservation(customer=self.customer, listing_id=other_listing.pk, quantity=1)
        with self.assertRaises(ReservationServiceError):
            mark_collected(reservation=other_reservation, actor=self.owner)


class ReservationViewTests(TestCase):
    def setUp(self):
        self.customer = User.objects.create_user(
            email="customer@example.com",
            password="StrongPass123!",
            name="Customer",
            role=User.Role.CUSTOMER,
        )
        owner = User.objects.create_user(
            email="owner@example.com",
            password="StrongPass123!",
            name="Owner",
            role=User.Role.RESTAURANT_OWNER,
        )
        restaurant = Restaurant.objects.create(owner=owner, name="Campus Bites", address="AIU")
        self.listing = FoodListing.objects.create(
            restaurant=restaurant,
            name="Nasi Lemak",
            original_price=Decimal("10.00"),
            discount_percentage=50,
            quantity=4,
            pickup_date=timezone.localdate(),
            pickup_start="21:00",
            pickup_end="23:00",
        )

    def test_customer_can_submit_reservation_and_view_confirmation(self):
        self.client.force_login(self.customer)
        response = self.client.post(
            reverse("reservations:create", kwargs={"listing_id": self.listing.pk}),
            {"quantity": 2},
        )
        self.assertEqual(response.status_code, 302)
        reservation = Reservation.objects.get(customer=self.customer)
        confirmation = self.client.get(response.url)
        self.assertContains(confirmation, "Reservation Confirmed")
        self.assertContains(confirmation, reservation.reservation_code)

