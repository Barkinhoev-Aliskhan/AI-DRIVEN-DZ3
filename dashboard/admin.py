from django.contrib import admin

from dashboard.models import Share


@admin.register(Share)
class ShareAdmin(admin.ModelAdmin):
    list_display = ("figi", "isin", "name", "ticker", "currency", "last_price")
    search_fields = ("figi", "isin", "name", "ticker")
    list_per_page = 50
