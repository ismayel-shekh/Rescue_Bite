from django.urls import path

from .views import detail, discover, home


app_name = "food"
urlpatterns = [
    path("", home, name="home"),
    path("discover/", discover, name="discover"),
    path("food/<int:pk>/", detail, name="detail"),
]
