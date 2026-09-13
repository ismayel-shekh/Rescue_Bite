from django.core.exceptions import ValidationError
from django.db import models


class Restaurant(models.Model):
    owner = models.OneToOneField(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="restaurant",
    )
    name = models.CharField(max_length=160)
    description = models.TextField(blank=True)
    address = models.CharField(max_length=240)
    location = models.CharField(max_length=160, blank=True)
    phone = models.CharField(max_length=30, blank=True)
    image = models.ImageField(upload_to="restaurants/", blank=True, null=True)
    image_url = models.URLField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def clean(self):
        if self.owner_id and self.owner.role != "RESTAURANT_OWNER":
            raise ValidationError({"owner": "Only restaurant owners can own a restaurant profile."})

    @property
    def display_image(self):
        if self.image:
            return self.image.url
        return self.image_url

    def __str__(self):
        return self.name
