from django.urls import path

from . import views

app_name = "dashboard"

urlpatterns = [
    path("", views.ShareListView.as_view(), name="index"),
    path("shares/<int:pk>/", views.ShareDetailView.as_view(), name="detail"),
    path("shares/create/", views.ShareCreateView.as_view(), name="create"),
    path("shares/<int:pk>/update/", views.ShareUpdateView.as_view(), name="update"),
    path("shares/<int:pk>/delete/", views.ShareDeleteView.as_view(), name="delete"),
    path("history/", views.PriceHistoryView.as_view(), name="history"),
]
