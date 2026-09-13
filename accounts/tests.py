from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


class AccountTests(TestCase):
    def test_create_user_normalizes_email_and_sets_role(self):
        user = get_user_model().objects.create_user(
            email=" Student@Example.com ",
            password="StrongPass123!",
            name="Aiman",
            role="CUSTOMER",
        )
        self.assertEqual(user.email, "student@example.com")
        self.assertEqual(user.role, "CUSTOMER")
        self.assertTrue(user.check_password("StrongPass123!"))

    def test_customer_registration_creates_profile(self):
        response = self.client.post(
            reverse("accounts:register"),
            {
                "email": "customer@example.com",
                "name": "Sarah",
                "role": "CUSTOMER",
                "password1": "StrongPass123!",
                "password2": "StrongPass123!",
            },
        )
        self.assertRedirects(response, reverse("food:discover"))
        user = get_user_model().objects.get(email="customer@example.com")
        self.assertTrue(hasattr(user, "customer_profile"))

    def test_owner_registration_redirects_to_restaurant_dashboard(self):
        response = self.client.post(
            reverse("accounts:register"),
            {
                "email": "owner@example.com",
                "name": "Owner",
                "role": "RESTAURANT_OWNER",
                "password1": "StrongPass123!",
                "password2": "StrongPass123!",
            },
        )
        self.assertRedirects(response, reverse("restaurants:dashboard"))

    def test_login_authenticates_customer(self):
        get_user_model().objects.create_user(
            email="customer@example.com",
            password="StrongPass123!",
            name="Sarah",
            role="CUSTOMER",
        )
        response = self.client.post(
            reverse("accounts:login"),
            {"username": "customer@example.com", "password": "StrongPass123!"},
        )
        self.assertRedirects(response, reverse("food:discover"))

    def test_restaurant_owner_cannot_open_customer_dashboard(self):
        owner = get_user_model().objects.create_user(
            email="owner@example.com",
            password="StrongPass123!",
            name="Owner",
            role="RESTAURANT_OWNER",
        )
        self.client.force_login(owner)
        response = self.client.get(reverse("accounts:customer_dashboard"))
        self.assertRedirects(response, reverse("restaurants:dashboard"))
