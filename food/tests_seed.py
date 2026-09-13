from io import StringIO

from django.core.management import call_command
from django.test import TestCase

from accounts.models import User
from food.models import FoodListing
from restaurants.models import Restaurant


class DemoSeedTests(TestCase):
    def test_seed_demo_creates_populated_platform(self):
        output = StringIO()
        call_command("seed_demo", stdout=output)
        self.assertGreaterEqual(FoodListing.objects.count(), 5)
        self.assertGreaterEqual(Restaurant.objects.count(), 3)
        self.assertIn("Demo data created", output.getvalue())

    def test_seed_demo_clear_can_reset_existing_demo_data(self):
        call_command("seed_demo")

        call_command("seed_demo", "--clear")

        admin = User.objects.get(email="admin@rescuebite.test")
        self.assertTrue(admin.is_staff)
        self.assertTrue(admin.check_password("admin"))
