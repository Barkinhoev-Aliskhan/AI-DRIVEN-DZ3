from django import forms

from .models import Share


class ShareModelForm(forms.ModelForm):
    """Форма инструмента."""

    class Meta:
        model = Share
        fields = ("figi", "isin", "name", "ticker", "currency", "uid", "last_price", "is_trend_high")
