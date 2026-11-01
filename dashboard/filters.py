from django_filters import rest_framework as filters

from dashboard.models import Share


class ShareFilter(filters.FilterSet):
    class Meta:
        model = Share
        fields = ("name", "ticker")
