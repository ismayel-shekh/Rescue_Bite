from decimal import Decimal

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import User
from food.models import FoodListing
from reservations.models import Reservation
from restaurants.models import Restaurant


class FinalCustomerFlowTests(TestCase):
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

    def test_customer_can_discover_reserve_and_view_confirmation(self):
        response = self.client.get(reverse("food:discover"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Nasi Lemak")
        self.client.force_login(self.customer)
        response = self.client.post(
            reverse("reservations:create", kwargs={"listing_id": self.listing.pk}),
            {"quantity": 1},
        )
        self.assertEqual(response.status_code, 302)
        confirmation = self.client.get(response.url)
        self.assertContains(confirmation, "Reservation Confirmed")
        self.assertEqual(Reservation.objects.filter(customer=self.customer).count(), 1)


class FinalPermissionFlowTests(TestCase):
    def test_customer_cannot_publish_food(self):
        customer = User.objects.create_user(
            email="customer@example.com",
            password="StrongPass123!",
            name="Customer",
            role=User.Role.CUSTOMER,
        )
        self.client.force_login(customer)
        response = self.client.get(reverse("restaurants:food_create"))
        self.assertRedirects(response, reverse("accounts:customer_dashboard"))
