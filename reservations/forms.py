from django import forms

from .models import Reservation


class ReservationForm(forms.ModelForm):
    class Meta:
        model = Reservation
        fields = ("quantity",)
        widgets = {"quantity": forms.NumberInput(attrs={"min": 1, "step": 1})}

    def __init__(self, *args, max_quantity=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.max_quantity = max_quantity
        if max_quantity is not None:
            self.fields["quantity"].widget.attrs["max"] = max_quantity

    def clean_quantity(self):
        quantity = self.cleaned_data["quantity"]
        if quantity < 1:
            raise forms.ValidationError("Choose at least one portion.")
        if self.max_quantity is not None and quantity > self.max_quantity:
            raise forms.ValidationError(f"Only {self.max_quantity} portion(s) remain available.")
        return quantity
