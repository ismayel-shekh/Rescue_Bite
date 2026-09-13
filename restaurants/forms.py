from django import forms

from .models import Restaurant


class RestaurantForm(forms.ModelForm):
    class Meta:
        model = Restaurant
        fields = ("name", "description", "address", "location", "phone", "image", "image_url")
        widgets = {
            "description": forms.Textarea(attrs={"rows": 4}),
        }
