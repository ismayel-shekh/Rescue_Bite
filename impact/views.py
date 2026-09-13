from django.shortcuts import render

from .services import get_platform_impact


def dashboard(request):
    return render(request, "impact/dashboard.html", {"impact": get_platform_impact()})
