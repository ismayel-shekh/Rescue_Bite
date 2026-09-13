from decimal import Decimal

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import User
from food.models import FoodListing
from reservations.models import Reservation
from reservations.services import create_reservation

from .models import Restaurant


class RestaurantFlowTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            email="owner@example.com",
            password="StrongPass123!",
            name="Owner",
            role=User.Role.RESTAURANT_OWNER,
        )
        self.customer = User.objects.create_user(
            email="customer@example.com",
            password="StrongPass123!",
            name="Customer",
            role=User.Role.CUSTOMER,
        )

    def test_owner_can_create_restaurant_and_food_listing(self):
        self.client.force_login(self.owner)
        profile_response = self.client.post(
            reverse("restaurants:profile"),
            {
                "name": "Green Bowl Kitchen",
                "description": "Fresh meals near campus.",
                "address": "Alor Setar",
                "location": "AIU Campus",
                "phone": "+60123456789",
            },
        )
        self.assertRedirects(profile_response, reverse("restaurants:dashboard"))
        restaurant = Restaurant.objects.get(owner=self.owner)
        response = self.client.post(
            reverse("restaurants:food_create"),
            {
                "name": "Nasi Lemak",
                "description": "Coconut rice with sambal.",
                "category": FoodListing.Category.RICE,
                "original_price": "10.00",
                "discount_percentage": "50",
                "quantity": "6",
                "pickup_date": timezone.localdate().isoformat(),
                "pickup_start": "21:00",
                "pickup_end": "22:00",
                "pickup_location": "AIU Hostel lobby",
            },
        )
        self.assertRedirects(response, reverse("restaurants:dashboard"))
        listing = FoodListing.objects.get(restaurant=restaurant)
        self.assertEqual(listing.discounted_price, Decimal("5.00"))

    def test_customer_cannot_open_restaurant_dashboard_or_create_food(self):
        self.client.force_login(self.customer)
        response = self.client.get(reverse("restaurants:dashboard"))
        self.assertRedirects(response, reverse("accounts:customer_dashboard"))
        response = self.client.get(reverse("restaurants:food_create"))
        self.assertRedirects(response, reverse("accounts:customer_dashboard"))

    def test_owner_dashboard_excludes_other_restaurants(self):
        other_owner = User.objects.create_user(
            email="other@example.com",
            password="StrongPass123!",
            name="Other",
            role=User.Role.RESTAURANT_OWNER,
        )
        other_restaurant = Restaurant.objects.create(owner=other_owner, name="Other Restaurant")
        FoodListing.objects.create(
            restaurant=other_restaurant,
            name="Other Food",
            original_price=Decimal("10.00"),
            discount_percentage=50,
            quantity=3,
            pickup_date=timezone.localdate(),
            pickup_start="21:00",
            pickup_end="22:00",
        )
        self.client.force_login(self.owner)
        response = self.client.get(reverse("restaurants:dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Other Food")

    def test_owner_reservation_page_shows_only_own_reservations(self):
        restaurant = Restaurant.objects.create(owner=self.owner, name="Campus Bites", address="AIU")
        other_owner = User.objects.create_user(
            email="other@example.com",
            password="StrongPass123!",
            name="Other",
            role=User.Role.RESTAURANT_OWNER,
        )
        other_restaurant = Restaurant.objects.create(owner=other_owner, name="Other Kitchen", address="AIU")
        customer = self.customer
        own_listing = FoodListing.objects.create(
            restaurant=restaurant,
            name="Own Food",
            original_price=Decimal("10.00"),
            discount_percentage=50,
            quantity=3,
            pickup_date=timezone.localdate(),
            pickup_start="21:00",
            pickup_end="23:00",
        )
        other_listing = FoodListing.objects.create(
            restaurant=other_restaurant,
            name="Other Food",
            original_price=Decimal("10.00"),
            discount_percentage=50,
            quantity=3,
            pickup_date=timezone.localdate(),
            pickup_start="21:00",
            pickup_end="23:00",
        )
        create_reservation(customer=customer, listing_id=own_listing.pk, quantity=1)
        create_reservation(customer=customer, listing_id=other_listing.pk, quantity=1)

        self.client.force_login(self.owner)
        response = self.client.get(reverse("restaurants:reservations"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Own Food")
        self.assertNotContains(response, "Other Food")

    def test_customer_cannot_open_restaurant_reservations(self):
        self.client.force_login(self.customer)
        response = self.client.get(reverse("restaurants:reservations"))
        self.assertRedirects(response, reverse("accounts:customer_dashboard"))

    def test_owner_can_mark_own_reservation_collected_from_dashboard(self):
        restaurant = Restaurant.objects.create(owner=self.owner, name="Campus Bites", address="AIU")
        listing = FoodListing.objects.create(
            restaurant=restaurant,
            name="Collected Food",
            original_price=Decimal("10.00"),
            discount_percentage=50,
            quantity=3,
            pickup_date=timezone.localdate(),
            pickup_start="21:00",
            pickup_end="23:00",
        )
        reservation = create_reservation(customer=self.customer, listing_id=listing.pk, quantity=1)
        self.client.force_login(self.owner)
        response = self.client.post(reverse("reservations:collect", kwargs={"pk": reservation.pk}))
        self.assertRedirects(response, reverse("restaurants:reservations"))
        reservation.refresh_from_db()
        self.assertEqual(reservation.status, Reservation.Status.COLLECTED)
