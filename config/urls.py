import os

from django.conf import settings
from django.contrib import admin
from django.http import HttpResponse
from django.urls import include, path

from .api import api


def health(request):
    return HttpResponse("OK")


admin_url = os.environ.get("DJANGO_ADMIN_URL", "admin")


urlpatterns = [
    path("api/", api.urls),
    path(f"{admin_url}/", admin.site.urls),
]


if settings.DEBUG:
    urlpatterns += [
        path("health/", health, name="health"),
        path("silk/", include("silk.urls", namespace="silk")),
    ]