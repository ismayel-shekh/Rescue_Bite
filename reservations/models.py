import secrets

from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


class Reservation(models.Model):
    class Status(models.TextChoices):
        RESERVED = "RESERVED", "Reserved"
        COLLECTED = "COLLECTED", "Collected"
        CANCELLED = "CANCELLED", "Cancelled"
        EXPIRED = "EXPIRED", "Expired"

    customer = models.ForeignKey(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="reservations",
    )
    food_listing = models.ForeignKey(
        "food.FoodListing",
        on_delete=models.PROTECT,
        related_name="reservations",
    )
    quantity = models.PositiveIntegerField()
    total_price = models.DecimalField(max_digits=8, decimal_places=2)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.RESERVED)
    reservation_code = models.CharField(max_length=16, unique=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    collected_at = models.DateTimeField(blank=True, null=True)
    cancelled_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["customer", "status"]),
            models.Index(fields=["food_listing", "status"]),
        ]

    def clean(self):
        if self.quantity is not None and self.quantity < 1:
            raise ValidationError({"quantity": "Reservation quantity must be at least one."})
        if self.customer_id and self.customer.role != "CUSTOMER":
            raise ValidationError({"customer": "Only customers can make reservations."})

    def save(self, *args, **kwargs):
        if not self.reservation_code:
            self.reservation_code = self._new_code()
        super().save(*args, **kwargs)

    @staticmethod
    def _new_code():
        return f"RB-{secrets.token_hex(4).upper()}"

    def mark_collected(self):
        self.status = self.Status.COLLECTED
        self.collected_at = timezone.now()

    def __str__(self):
        return self.reservation_code
