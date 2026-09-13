from decimal import Decimal

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import User
from food.models import FoodListing
from reservations.services import create_reservation, mark_collected
from restaurants.models import Restaurant

from .models import Review


class ReviewTests(TestCase):
    def setUp(self):
        self.customer = User.objects.create_user(
            email="customer@example.com",
            password="StrongPass123!",
            name="Customer",
            role=User.Role.CUSTOMER,
        )
        self.other_customer = User.objects.create_user(
            email="other@example.com",
            password="StrongPass123!",
            name="Other",
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
            quantity=5,
            pickup_date=timezone.localdate(),
            pickup_start="21:00",
            pickup_end="23:00",
        )

    def make_collected_reservation(self):
        reservation = create_reservation(customer=self.customer, listing_id=self.listing.pk, quantity=1)
        return mark_collected(reservation=reservation, actor=self.restaurant.owner)

    def test_customer_can_review_collected_reservation(self):
        reservation = self.make_collected_reservation()
        self.client.force_login(self.customer)
        response = self.client.post(
            reverse("reviews:create", kwargs={"reservation_id": reservation.pk}),
            {"rating": 5, "comment": "Fresh and affordable."},
        )
        self.assertRedirects(response, reverse("food:detail", kwargs={"pk": self.listing.pk}))
        review = Review.objects.get()
        self.assertEqual(review.restaurant, self.restaurant)
        self.assertEqual(review.rating, 5)

    def test_customer_cannot_review_reserved_reservation(self):
        reservation = create_reservation(customer=self.customer, listing_id=self.listing.pk, quantity=1)
        self.client.force_login(self.customer)
        response = self.client.post(
            reverse("reviews:create", kwargs={"reservation_id": reservation.pk}),
            {"rating": 5, "comment": "Not collected yet."},
        )
        self.assertRedirects(response, reverse("reservations:customer_list"))
        self.assertEqual(Review.objects.count(), 0)

    def test_customer_cannot_review_another_customers_reservation(self):
        reservation = self.make_collected_reservation()
        self.client.force_login(self.other_customer)
        response = self.client.get(reverse("reviews:create", kwargs={"reservation_id": reservation.pk}))
        self.assertEqual(response.status_code, 404)

    def test_one_review_is_allowed_per_reservation(self):
        reservation = self.make_collected_reservation()
        self.client.force_login(self.customer)
        url = reverse("reviews:create", kwargs={"reservation_id": reservation.pk})
        self.client.post(url, {"rating": 5, "comment": "Great."})
        response = self.client.post(url, {"rating": 4, "comment": "Updated."})
        self.assertRedirects(response, reverse("food:detail", kwargs={"pk": self.listing.pk}))
        self.assertEqual(Review.objects.count(), 1)

