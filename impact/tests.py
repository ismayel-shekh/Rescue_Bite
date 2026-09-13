from decimal import Decimal

from django.test import TestCase
from django.utils import timezone

from accounts.models import User
from food.models import FoodListing
from reservations.services import create_reservation, mark_collected
from restaurants.models import Restaurant

from .services import get_customer_impact, get_platform_impact, get_restaurant_impact


class ImpactServiceTests(TestCase):
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
        self.restaurant = Restaurant.objects.create(owner=owner, name="Campus Bites", address="AIU")
        self.listing = FoodListing.objects.create(
            restaurant=self.restaurant,
            name="Chicken Biryani",
            original_price=Decimal("10.00"),
            discount_percentage=50,
            quantity=8,
            pickup_date=timezone.localdate(),
            pickup_start="21:00",
            pickup_end="23:00",
        )

    def test_impact_counts_collected_meals_only(self):
        collected = create_reservation(customer=self.customer, listing_id=self.listing.pk, quantity=2)
        mark_collected(reservation=collected, actor=self.restaurant.owner)
        create_reservation(customer=self.customer, listing_id=self.listing.pk, quantity=3)

        impact = get_platform_impact()
        self.assertEqual(impact["meals_served"], 2)
        self.assertEqual(impact["food_saved_kg"], Decimal("1.00"))
        self.assertEqual(impact["co2_avoided_kg"], Decimal("2.00"))
        self.assertEqual(impact["customer_savings"], Decimal("10.00"))
        self.assertEqual(impact["restaurants"], 1)

    def test_customer_and_restaurant_impact_are_scoped(self):
        reservation = create_reservation(customer=self.customer, listing_id=self.listing.pk, quantity=1)
        mark_collected(reservation=reservation, actor=self.restaurant.owner)
        self.assertEqual(get_customer_impact(self.customer)["meals_served"], 1)
        self.assertEqual(get_restaurant_impact(self.restaurant)["meals_served"], 1)

