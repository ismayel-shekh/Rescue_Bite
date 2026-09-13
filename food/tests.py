from datetime import timedelta
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import User
from restaurants.models import Restaurant

from .models import FoodListing


class FoodListingTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            email="owner@example.com",
            password="StrongPass123!",
            name="Owner",
            role=User.Role.RESTAURANT_OWNER,
        )
        self.restaurant = Restaurant.objects.create(
            owner=self.owner,
            name="Campus Bites",
            address="Alor Setar",
            location="AIU Campus",
        )

    def make_listing(self, **overrides):
        values = {
            "restaurant": self.restaurant,
            "name": "Chicken Biryani",
            "description": "A fragrant rice meal.",
            "category": FoodListing.Category.RICE,
            "original_price": Decimal("12.00"),
            "discount_percentage": 50,
            "quantity": 8,
            "pickup_date": timezone.localdate(),
            "pickup_start": timezone.datetime(2026, 9, 11, 21, 0).time(),
            "pickup_end": timezone.datetime(2026, 9, 11, 22, 0).time(),
            "pickup_location": "AIU Hostel lobby",
        }
        values.update(overrides)
        return FoodListing.objects.create(**values)

    def test_discounted_price_is_calculated_from_original_price(self):
        listing = FoodListing(original_price=Decimal("12.00"), discount_percentage=50)
        self.assertEqual(listing.calculate_discounted_price(), Decimal("6.00"))

    def test_discount_outside_forty_to_sixty_is_rejected(self):
        listing = FoodListing(
            restaurant=self.restaurant,
            name="Rice",
            original_price=Decimal("10.00"),
            discount_percentage=35,
            quantity=1,
            pickup_date=timezone.localdate(),
            pickup_start=timezone.datetime(2026, 9, 11, 21, 0).time(),
            pickup_end=timezone.datetime(2026, 9, 11, 22, 0).time(),
        )
        with self.assertRaises(ValidationError):
            listing.full_clean()

    def test_expired_listing_changes_to_expired_status(self):
        yesterday = timezone.localdate() - timedelta(days=1)
        listing = self.make_listing(pickup_date=yesterday)
        listing.refresh_status()
        self.assertEqual(listing.status, FoodListing.Status.EXPIRED)

    def test_zero_quantity_listing_changes_to_sold_out_status(self):
        listing = self.make_listing(quantity=0)
        listing.refresh_status()
        self.assertEqual(listing.status, FoodListing.Status.SOLD_OUT)

    def test_discover_filters_by_search_and_discount(self):
        self.make_listing(name="Chicken Biryani", discount_percentage=50)
        self.make_listing(name="Nasi Lemak", discount_percentage=40)
        response = self.client.get(
            reverse("food:discover"),
            {"q": "biryani", "min_discount": "50"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Chicken Biryani")
        self.assertNotContains(response, "Nasi Lemak")

