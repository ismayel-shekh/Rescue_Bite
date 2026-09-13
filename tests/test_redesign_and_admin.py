from io import StringIO
from decimal import Decimal

from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone

from accounts.models import User
from food.models import FoodListing
from restaurants.models import Restaurant


class HomepageRedesignTests(TestCase):
    def test_homepage_contains_restaurant_style_sections(self):
        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "About Rescue Bite")
        self.assertContains(response, "Breakfast")
        self.assertContains(response, "Lunch")
        self.assertContains(response, "Dinner")
        self.assertContains(response, "Our community says")


class AdminDashboardTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            email="admin@rescuebite.test",
            password="admin",
            name="Admin",
            role=User.Role.RESTAURANT_OWNER,
            is_staff=True,
            is_superuser=True,
        )
        owner = User.objects.create_user(
            email="owner@example.com",
            password="StrongPass123!",
            name="Owner",
            role=User.Role.RESTAURANT_OWNER,
        )
        restaurant = Restaurant.objects.create(
            owner=owner,
            name="Campus Bites",
            location="AIU Campus",
            address="Alor Setar",
        )
        FoodListing.objects.create(
            restaurant=restaurant,
            name="Nasi Lemak",
            original_price=Decimal("10.00"),
            discount_percentage=50,
            quantity=5,
            pickup_date=timezone.localdate(),
            pickup_start="18:00",
            pickup_end="20:00",
        )

    def test_staff_user_can_view_admin_dashboard(self):
        self.client.force_login(self.admin)

        response = self.client.get("/admin-dashboard/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Admin Dashboard")
        self.assertContains(response, "Total customers")
        self.assertContains(response, "Active listings")
        self.assertContains(response, "Campus Bites")
        self.assertNotContains(response, "site-header--overlay")

    def test_non_staff_user_cannot_view_admin_dashboard(self):
        customer = User.objects.create_user(
            email="customer@example.com",
            password="StrongPass123!",
            name="Customer",
            role=User.Role.CUSTOMER,
        )
        self.client.force_login(customer)

        response = self.client.get("/admin-dashboard/")

        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts/login/", response.url)

    def test_admin_credentials_redirect_to_custom_dashboard(self):
        response = self.client.post(
            "/accounts/login/",
            {"username": "admin@rescuebite.test", "password": "admin"},
        )

        self.assertRedirects(response, "/admin-dashboard/")

    def test_seed_demo_creates_local_admin_credentials(self):
        User.objects.filter(email=self.admin.email).delete()

        call_command("seed_demo", "--clear", stdout=StringIO())

        admin = User.objects.get(email="admin@rescuebite.test")
        self.assertEqual(admin.name, "Admin")
        self.assertTrue(admin.is_staff)
        self.assertTrue(admin.is_superuser)
        self.assertTrue(admin.check_password("admin"))


class WorkspaceRedesignTests(TestCase):
    def setUp(self):
        self.customer = User.objects.create_user(
            email="customer@example.com",
            password="StrongPass123!",
            name="Nayem Student",
            role=User.Role.CUSTOMER,
        )
        self.owner = User.objects.create_user(
            email="owner@example.com",
            password="StrongPass123!",
            name="Campus Bites Owner",
            role=User.Role.RESTAURANT_OWNER,
        )
        self.restaurant = Restaurant.objects.create(
            owner=self.owner,
            name="Campus Bites",
            location="AIU Campus",
            address="Alor Setar",
        )
        self.listing = FoodListing.objects.create(
            restaurant=self.restaurant,
            name="Nasi Lemak",
            category=FoodListing.Category.RICE,
            original_price=Decimal("10.00"),
            discount_percentage=50,
            quantity=5,
            pickup_date=timezone.localdate(),
            pickup_start="18:00",
            pickup_end="20:00",
        )

    def test_customer_dashboard_matches_reference_workspace(self):
        self.client.force_login(self.customer)

        response = self.client.get("/accounts/customer/dashboard/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "rb-customer-workspace")
        self.assertContains(response, "Food discovery")
        self.assertContains(response, "My reservations")
        self.assertContains(response, "Notifications")
        self.assertContains(response, "Personalized impact")
        self.assertContains(response, "Nasi Lemak")

    def test_customer_discovery_uses_reference_food_grid(self):
        self.client.force_login(self.customer)

        response = self.client.get("/discover/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "rb-customer-workspace")
        self.assertContains(response, "Food discovery")
        self.assertContains(response, "Search food")
        self.assertContains(response, "Reserve now")

    def test_customer_profile_editor_uses_reference_workspace(self):
        self.client.force_login(self.customer)

        response = self.client.get("/accounts/profile/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "rb-customer-workspace")
        self.assertContains(response, "Profile settings")

    def test_restaurant_dashboard_matches_reference_workspace(self):
        self.client.force_login(self.owner)

        response = self.client.get("/restaurants/dashboard/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "rb-restaurant-workspace")
        self.assertContains(response, "Listing creation")
        self.assertContains(response, "Inventory management")
        self.assertContains(response, "Restaurant impact")
        self.assertContains(response, "Nasi Lemak")

    def test_restaurant_listing_form_uses_reference_workspace(self):
        self.client.force_login(self.owner)

        response = self.client.get("/restaurants/food/add/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "rb-restaurant-workspace")
        self.assertContains(response, "Listing creation")
        self.assertContains(response, "Publish food")

    def test_customer_reservations_use_reference_workspace(self):
        self.client.force_login(self.customer)

        response = self.client.get("/reservations/my/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "rb-customer-workspace")
        self.assertContains(response, "My reservations")

    def test_notifications_use_reference_workspace(self):
        self.client.force_login(self.customer)

        response = self.client.get("/notifications/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "rb-customer-workspace")
        self.assertContains(response, "Notifications")

    def test_restaurant_reservations_use_reference_workspace(self):
        self.client.force_login(self.owner)

        response = self.client.get("/restaurants/reservations/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "rb-restaurant-workspace")
        self.assertContains(response, "Reservation management")

    def test_restaurant_profile_form_uses_reference_workspace(self):
        self.client.force_login(self.owner)

        response = self.client.get("/restaurants/profile/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "rb-restaurant-workspace")
        self.assertContains(response, "Restaurant profile")
