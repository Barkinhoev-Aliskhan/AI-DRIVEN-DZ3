from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("dashboard.urls")),
    path("user/", include("user.urls")),
    path("tracker/", include("tracker.urls")),
    path("api/", include("dashboard.api.urls")),
]
