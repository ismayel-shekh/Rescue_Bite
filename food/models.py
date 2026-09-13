from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP

from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


class FoodListing(models.Model):
    class Category(models.TextChoices):
        RICE = "RICE", "Rice"
        NOODLES = "NOODLES", "Noodles"
        CHICKEN = "CHICKEN", "Chicken"
        FAST_FOOD = "FAST_FOOD", "Fast Food"
        BAKERY = "BAKERY", "Bakery"
        DESSERT = "DESSERT", "Dessert"
        DRINKS = "DRINKS", "Drinks"
        OTHER = "OTHER", "Other"

    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        SOLD_OUT = "SOLD_OUT", "Sold Out"
        EXPIRED = "EXPIRED", "Expired"

    restaurant = models.ForeignKey("restaurants.Restaurant", on_delete=models.CASCADE, related_name="food_listings")
    name = models.CharField(max_length=160)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=30, choices=Category.choices, default=Category.OTHER)
    image = models.ImageField(upload_to="food/", blank=True, null=True)
    image_url = models.URLField(blank=True)
    original_price = models.DecimalField(max_digits=8, decimal_places=2)
    discount_percentage = models.PositiveSmallIntegerField(default=50)
    discounted_price = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal("0.00"))
    quantity = models.PositiveIntegerField(default=1)
    pickup_date = models.DateField(default=timezone.localdate)
    pickup_start = models.TimeField()
    pickup_end = models.TimeField()
    pickup_location = models.CharField(max_length=240, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["pickup_date", "pickup_end", "-created_at"]
        indexes = [
            models.Index(fields=["status", "pickup_date"]),
            models.Index(fields=["category", "status"]),
            models.Index(fields=["restaurant", "status"]),
        ]

    def calculate_discounted_price(self):
        multiplier = Decimal("1") - (Decimal(self.discount_percentage) / Decimal("100"))
        return (self.original_price * multiplier).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    def clean(self):
        errors = {}
        if self.original_price is not None and self.original_price <= 0:
            errors["original_price"] = "Original price must be greater than zero."
        if self.discount_percentage is not None and not 40 <= self.discount_percentage <= 60:
            errors["discount_percentage"] = "Discount must be between 40% and 60%."
        if self.quantity is not None and self.quantity < 0:
            errors["quantity"] = "Quantity cannot be negative."
        if self.pickup_start and self.pickup_end and self.pickup_end <= self.pickup_start:
            errors["pickup_end"] = "Pickup end time must be after pickup start time."
        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.discounted_price = self.calculate_discounted_price()
        super().save(*args, **kwargs)

    def end_datetime(self):
        naive_end = datetime.combine(self.pickup_date, self.pickup_end)
        return timezone.make_aware(naive_end, timezone.get_current_timezone())

    def is_expired(self, at=None):
        at = at or timezone.now()
        if timezone.is_naive(at):
            at = timezone.make_aware(at, timezone.get_current_timezone())
        return at >= self.end_datetime()

    def refresh_status(self, at=None):
        next_status = self.status
        if self.status == self.Status.ACTIVE:
            if self.quantity == 0:
                next_status = self.Status.SOLD_OUT
            elif self.is_expired(at):
                next_status = self.Status.EXPIRED
        if next_status != self.status:
            self.status = next_status
            self.save(update_fields=["status", "updated_at"])
        return self

    @property
    def display_image(self):
        if self.image:
            return self.image.url
        return self.image_url

    @property
    def is_low_stock(self):
        return 0 < self.quantity <= 3

    def __str__(self):
        return self.name
