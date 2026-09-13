from django import forms
from django.utils import timezone

from .models import FoodListing


class FoodListingForm(forms.ModelForm):
    class Meta:
        model = FoodListing
        fields = (
            "name",
            "description",
            "category",
            "image",
            "image_url",
            "original_price",
            "discount_percentage",
            "quantity",
            "pickup_date",
            "pickup_start",
            "pickup_end",
            "pickup_location",
        )
        widgets = {
            "description": forms.Textarea(attrs={"rows": 4}),
            "pickup_date": forms.DateInput(attrs={"type": "date"}),
            "pickup_start": forms.TimeInput(attrs={"type": "time"}),
            "pickup_end": forms.TimeInput(attrs={"type": "time"}),
            "discount_percentage": forms.NumberInput(attrs={"min": 40, "max": 60, "step": 5}),
            "original_price": forms.NumberInput(attrs={"min": 0.01, "step": "0.01"}),
            "quantity": forms.NumberInput(attrs={"min": 1, "step": 1}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.instance.pk and not self.initial.get("pickup_date"):
            self.initial["pickup_date"] = timezone.localdate()

    def clean_discount_percentage(self):
        discount = self.cleaned_data["discount_percentage"]
        if not 40 <= discount <= 60:
            raise forms.ValidationError("Choose a discount between 40% and 60%.")
        return discount

    def clean_quantity(self):
        quantity = self.cleaned_data["quantity"]
        if quantity < 1:
            raise forms.ValidationError("Available quantity must be at least 1.")
        return quantity

    def clean(self):
        cleaned = super().clean()
        start = cleaned.get("pickup_start")
        end = cleaned.get("pickup_end")
        if start and end and end <= start:
            self.add_error("pickup_end", "Pickup end time must be after pickup start time.")
        return cleaned
