from django.urls import path

from .views import index, mark_read


app_name = "notifications"
urlpatterns = [
    path("", index, name="index"),
    path("<int:pk>/read/", mark_read, name="mark_read"),
]
