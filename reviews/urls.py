from django.urls import path

from .views import create


app_name = "reviews"
urlpatterns = [path("reservation/<int:reservation_id>/create/", create, name="create")]
