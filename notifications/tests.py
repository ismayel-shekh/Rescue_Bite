from decimal import Decimal

from django.test import TestCase
from django.utils import timezone

from accounts.models import User
from food.models import FoodListing
from restaurants.models import Restaurant
from reservations.services import create_reservation

from .models import Notification
from .services import notify_new_listing


class NotificationTests(TestCase):
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
            quantity=5,
            pickup_date=timezone.localdate(),
            pickup_start="21:00",
            pickup_end="23:00",
        )

    def test_reservation_creates_customer_notification(self):
        create_reservation(customer=self.customer, listing_id=self.listing.pk, quantity=1)
        notification = Notification.objects.get(customer=self.customer)
        self.assertEqual(notification.notification_type, Notification.Type.RESERVATION)
        self.assertIn("Nasi Lemak", notification.message)

    def test_notification_manager_filters_customer_and_unread_items(self):
        Notification.objects.create(
            customer=self.customer,
            title="Unread",
            message="Unread message",
            notification_type=Notification.Type.NEW_FOOD,
        )
        other = User.objects.create_user(
            email="other@example.com",
            password="StrongPass123!",
            name="Other",
            role=User.Role.CUSTOMER,
        )
        Notification.objects.create(
            customer=other,
            title="Other",
            message="Other message",
            notification_type=Notification.Type.NEW_FOOD,
        )
        self.assertEqual(Notification.objects.for_customer(self.customer).count(), 1)
        self.assertEqual(Notification.objects.unread_for(self.customer).count(), 1)

    def test_new_listing_notifies_active_customers(self):
        notify_new_listing(self.listing)
        notification = Notification.objects.get(customer=self.customer)
        self.assertEqual(notification.notification_type, Notification.Type.NEW_FOOD)
        self.assertIn("50% OFF", notification.message)

