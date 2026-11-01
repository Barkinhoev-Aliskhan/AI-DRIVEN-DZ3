from django import forms

from dashboard.models import Share

from .models import Portfolio, Strategy, Transaction, WatchItem


class WatchItemForm(forms.ModelForm):
    """Форма наблюдения (FR-20, FR-21)."""

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

    class Meta:
        model = WatchItem
        fields = ("share", "target_price", "direction")
        widgets = {
            "target_price": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "direction": forms.Select(attrs={"class": "form-select"}),
        }

    def clean(self):
        cleaned = super().clean()
        share = cleaned.get("share")
        target = cleaned.get("target_price")
        if target is not None and target <= 0:
            self.add_error("target_price", "Целевая цена должна быть положительной")
        if share and self.user and self.instance.pk is None:
            if WatchItem.objects.filter(user=self.user, share=share).exists():
                self.add_error("share", "Наблюдение для этой акции уже создано")
        return cleaned


class PortfolioForm(forms.ModelForm):
    """Форма портфеля (FR-25)."""

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

    class Meta:
        model = Portfolio
        fields = ("name",)
        widgets = {"name": forms.TextInput(attrs={"class": "form-control"})}

    def clean_name(self):
        name = self.cleaned_data["name"].strip()
        if self.user:
            exists = Portfolio.objects.filter(user=self.user, name__iexact=name)
            if self.instance.pk:
                exists = exists.exclude(pk=self.instance.pk)
            if exists.exists():
                raise forms.ValidationError("Портфель с таким названием уже существует")
        return name


class TransactionForm(forms.ModelForm):
    """Форма операции: продажа сверх остатка блокируется (FR-27)."""

    def __init__(self, *args, portfolio=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.portfolio = portfolio

    class Meta:
        model = Transaction
        fields = ("action", "share", "quantity", "price")
        widgets = {
            "action": forms.Select(attrs={"class": "form-select"}),
            "share": forms.Select(attrs={"class": "form-select"}),
            "quantity": forms.NumberInput(attrs={"class": "form-control", "min": "1"}),
            "price": forms.NumberInput(attrs={"class": "form-control", "step": "0.01", "min": "0"}),
        }

    def clean(self):
        from tracker.logic import calculate_position

        cleaned = super().clean()
        action = cleaned.get("action")
        share = cleaned.get("share")
        quantity = cleaned.get("quantity")
        price = cleaned.get("price")

        if price is not None and price <= 0:
            self.add_error("price", "Цена должна быть положительной")

        if action == "sell" and share and self.portfolio and quantity:
            positions, _ = calculate_position(self.portfolio.transactions.filter(share=share))
            qty, _avg = positions.get(share.id, (0.0, 0.0))
            if quantity > qty:
                self.add_error(
                    "quantity",
                    f"В портфеле только {int(qty)} шт. {share.ticker} — продать нельзя",
                )
        return cleaned


class StrategyForm(forms.ModelForm):
    """Форма стратегии (FR-35)."""

    class Meta:
        model = Strategy
        fields = ("share", "action", "trigger_price", "quantity", "trades_limit")
        widgets = {
            "action": forms.Select(attrs={"class": "form-select"}),
            "share": forms.Select(attrs={"class": "form-select"}),
            "trigger_price": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "quantity": forms.NumberInput(attrs={"class": "form-control", "min": "1"}),
            "trades_limit": forms.NumberInput(attrs={"class": "form-control", "min": "1"}),
        }

    def clean(self):
        cleaned = super().clean()
        trigger = cleaned.get("trigger_price")
        if trigger is not None and trigger <= 0:
            self.add_error("trigger_price", "Триггерная цена должна быть положительной")
        return cleaned
