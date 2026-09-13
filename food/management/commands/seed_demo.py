from datetime import timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from accounts.models import User
from notifications.models import Notification
from reservations.models import Reservation
from reservations.services import create_reservation, mark_collected
from reviews.models import Review
from restaurants.models import Restaurant

from food.models import FoodListing


DEMO_OWNER_EMAILS = [
    "greenbowl@rescuebite.test",
    "nasihouse@rescuebite.test",
    "campusbites@rescuebite.test",
    "spicecorner@rescuebite.test",
    "urbanplate@rescuebite.test",
]
DEMO_CUSTOMER_EMAIL = "student@rescuebite.test"
DEMO_ADMIN_EMAIL = "admin@rescuebite.test"


class Command(BaseCommand):
    help = "Create realistic demo data for the Rescue Bite university prototype."

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Remove only the Rescue Bite demo records before recreating them.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        if options["clear"]:
            demo_users = User.objects.filter(
                email__in=[*DEMO_OWNER_EMAILS, DEMO_CUSTOMER_EMAIL, DEMO_ADMIN_EMAIL],
            )
            demo_restaurants = Restaurant.objects.filter(owner__in=demo_users)
            demo_listings = FoodListing.objects.filter(restaurant__in=demo_restaurants)
            Reservation.objects.filter(
                Q(customer__in=demo_users) | Q(food_listing__in=demo_listings),
            ).delete()
            demo_users.delete()

        admin, _ = User.objects.get_or_create(
            email=DEMO_ADMIN_EMAIL,
            defaults={
                "name": "Admin",
                "role": User.Role.RESTAURANT_OWNER,
                "is_staff": True,
                "is_superuser": True,
            },
        )
        admin.name = "Admin"
        admin.role = User.Role.RESTAURANT_OWNER
        admin.is_active = True
        admin.is_staff = True
        admin.is_superuser = True
        admin.set_password("admin")
        admin.save(update_fields=["name", "role", "is_active", "is_staff", "is_superuser", "password"])

        owners = {}
        restaurant_data = [
            ("greenbowl@rescuebite.test", "Green Bowl Kitchen", "Fresh rice bowls and healthy meals.", "AIU Campus", "Alor Setar"),
            ("nasihouse@rescuebite.test", "Nasi House", "Comforting Malaysian favourites.", "Anak Bukit", "Alor Setar"),
            ("campusbites@rescuebite.test", "Campus Bites", "Student-friendly meals near the hostel.", "AIU Hostel", "Alor Setar"),
            ("spicecorner@rescuebite.test", "Spice Corner", "Warm Malaysian and South Asian dishes.", "Mergong", "Alor Setar"),
            ("urbanplate@rescuebite.test", "Urban Plate", "Modern comfort food prepared daily.", "Tandop", "Alor Setar"),
        ]
        for email, name, description, location, address in restaurant_data:
            owner, _ = User.objects.get_or_create(
                email=email,
                defaults={"name": f"{name} Owner", "role": User.Role.RESTAURANT_OWNER},
            )
            owner.name = f"{name} Owner"
            owner.role = User.Role.RESTAURANT_OWNER
            owner.set_password("RescueBiteDemo123!")
            owner.save(update_fields=["name", "role", "password"])
            restaurant, _ = Restaurant.objects.update_or_create(
                owner=owner,
                defaults={
                    "name": name,
                    "description": description,
                    "location": location,
                    "address": address,
                    "phone": "+60123456789",
                },
            )
            owners[email] = restaurant

        customer, _ = User.objects.get_or_create(
            email=DEMO_CUSTOMER_EMAIL,
            defaults={"name": "Aiman Rahman", "role": User.Role.CUSTOMER},
        )
        customer.name = "Aiman Rahman"
        customer.role = User.Role.CUSTOMER
        customer.set_password("RescueBiteDemo123!")
        customer.save(update_fields=["name", "role", "password"])

        tomorrow = timezone.localdate() + timedelta(days=1)
        listing_data = [
            ("greenbowl@rescuebite.test", "Chicken Biryani", FoodListing.Category.RICE, "Fragrant chicken biryani with cucumber salad.", "12.00", 50, 12, "https://images.unsplash.com/photo-1589302168068-964664d93dc0?auto=format&fit=crop&w=1200&q=85"),
            ("nasihouse@rescuebite.test", "Nasi Lemak", FoodListing.Category.RICE, "Coconut rice with sambal, egg, and crispy anchovies.", "10.00", 50, 10, "https://images.unsplash.com/photo-1603133872878-684f208fb84b?auto=format&fit=crop&w=1200&q=85"),
            ("campusbites@rescuebite.test", "Chicken Burger", FoodListing.Category.FAST_FOOD, "Juicy chicken burger with fresh lettuce.", "15.00", 40, 8, "https://images.unsplash.com/photo-1568901346375-23c9450c58cd?auto=format&fit=crop&w=1200&q=85"),
            ("spicecorner@rescuebite.test", "Fried Chicken", FoodListing.Category.CHICKEN, "Crispy fried chicken pieces prepared for the evening.", "14.00", 60, 9, "https://images.unsplash.com/photo-1626082927389-6cd097cdc6ec?auto=format&fit=crop&w=1200&q=85"),
            ("urbanplate@rescuebite.test", "Creamy Pasta", FoodListing.Category.NOODLES, "Creamy pasta with herbs and roasted vegetables.", "16.00", 50, 7, "https://images.unsplash.com/photo-1551892374-ecf8754cf8b0?auto=format&fit=crop&w=1200&q=85"),
            ("greenbowl@rescuebite.test", "Vegetable Rice Bowl", FoodListing.Category.RICE, "Colourful vegetables over seasoned rice.", "11.00", 40, 6, "https://images.unsplash.com/photo-1512621776951-a57141f2e346?auto=format&fit=crop&w=1200&q=85"),
        ]
        listings = []
        for email, name, category, description, original_price, discount, quantity, image_url in listing_data:
            listing, _ = FoodListing.objects.update_or_create(
                restaurant=owners[email],
                name=name,
                defaults={
                    "description": description,
                    "category": category,
                    "original_price": Decimal(original_price),
                    "discount_percentage": discount,
                    "quantity": quantity,
                    "pickup_date": tomorrow,
                    "pickup_start": "21:00",
                    "pickup_end": "22:00",
                    "pickup_location": owners[email].location,
                    "image_url": image_url,
                    "status": FoodListing.Status.ACTIVE,
                },
            )
            listings.append(listing)

        first_listing = listings[0]
        reservation = Reservation.objects.filter(customer=customer, food_listing=first_listing).first()
        if not reservation:
            reservation = create_reservation(customer=customer, listing_id=first_listing.pk, quantity=1)
        if reservation.status == Reservation.Status.RESERVED:
            mark_collected(reservation=reservation, actor=first_listing.restaurant.owner)
        Review.objects.get_or_create(
            reservation=reservation,
            defaults={
                "customer": customer,
                "restaurant": first_listing.restaurant,
                "food_listing": first_listing,
                "rating": 5,
                "comment": "Fresh, affordable, and easy to collect before closing.",
            },
        )
        Notification.objects.get_or_create(
            customer=customer,
            title="Welcome to Rescue Bite",
            defaults={
                "message": "Find affordable food while helping reduce waste.",
                "notification_type": Notification.Type.NEW_FOOD,
            },
        )

        self.stdout.write(self.style.SUCCESS("Demo data created."))
