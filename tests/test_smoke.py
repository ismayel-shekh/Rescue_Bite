from django.test import TestCase
from django.urls import reverse


class ProjectSmokeTests(TestCase):
    def test_homepage_is_reachable(self):
        response = self.client.get(reverse("food:home"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Rescue Bite")
