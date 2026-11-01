from django.urls import include, path

urlpatterns = [
    path("api/v1/", include("dashboard.api.v1.urls")),
]
