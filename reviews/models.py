from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Review(models.Model):
    customer = models.ForeignKey("accounts.User", on_delete=models.CASCADE, related_name="reviews")
    restaurant = models.ForeignKey("restaurants.Restaurant", on_delete=models.CASCADE, related_name="reviews")
    food_listing = models.ForeignKey("food.FoodListing", on_delete=models.CASCADE, related_name="reviews")
    reservation = models.OneToOneField("reservations.Reservation", on_delete=models.CASCADE, related_name="review")
    rating = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.TextField(max_length=1200)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["restaurant", "created_at"])]

    def clean(self):
        errors = {}
        if self.reservation_id:
            reservation = self.reservation
            if reservation.customer_id != self.customer_id:
                errors["customer"] = "This reservation belongs to another customer."
            if reservation.food_listing_id != self.food_listing_id:
                errors["food_listing"] = "The food listing does not match the reservation."
            if reservation.status != "COLLECTED":
                errors["reservation"] = "You can review a meal only after it is collected."
        if self.restaurant_id and self.food_listing_id and self.food_listing.restaurant_id != self.restaurant_id:
            errors["restaurant"] = "The restaurant does not match the food listing."
        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return f"{self.rating}/5 by {self.customer.name}"
