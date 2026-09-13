from django.urls import path

from .views import dashboard, food_create, food_delete, food_edit, profile, reservation_list


app_name = "restaurants"
urlpatterns = [
    path("dashboard/", dashboard, name="dashboard"),
    path("profile/", profile, name="profile"),
    path("food/add/", food_create, name="food_create"),
    path("food/<int:pk>/edit/", food_edit, name="food_edit"),
    path("food/<int:pk>/delete/", food_delete, name="food_delete"),
    path("reservations/", reservation_list, name="reservations"),
]
