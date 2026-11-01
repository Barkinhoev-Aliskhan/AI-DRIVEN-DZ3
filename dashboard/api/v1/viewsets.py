from django_filters import rest_framework as filters
from rest_framework import viewsets
from rest_framework.filters import OrderingFilter, SearchFilter

from dashboard.api.v1.filters import ShareFilter
from dashboard.api.v1.serializers import ShareSerializer
from dashboard.models import Share


class ShareViewSet(viewsets.ModelViewSet):
    """CRUD API для акций: фильтрация, поиск и сортировка."""

    serializer_class = ShareSerializer
    queryset = Share.objects.all()
    filter_backends = (OrderingFilter, filters.DjangoFilterBackend, SearchFilter)
    filterset_class = ShareFilter
    ordering_fields = ["name", "ticker", "updated_at"]
    search_fields = ["$name", "$ticker", "figi", "isin"]
