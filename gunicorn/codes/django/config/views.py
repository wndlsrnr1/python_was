from django.http import JsonResponse
from django.contrib import admin
from django.urls import path
from myapp.views import index
from config import settings

settings.setattr("ALLOWED_HOSTS") = ["localhost", "127.0.0.1", "your-domain.com"]


def index(request):
    return JsonResponse({
        "message": "Hello from Django with Gunicorn",
        "method": request.method
    })

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", index)
]

