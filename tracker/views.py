from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, ListView, View

from dashboard.models import Share

from .forms import PortfolioForm, StrategyForm, TransactionForm, WatchItemForm
from .logic import calculate_position
from .models import Notification, Portfolio, Strategy, Transaction, WatchItem
from .services import run_strategy


class WatchListView(LoginRequiredMixin, ListView):
    """Список наблюдений пользователя (FR-20)."""

    template_name = "tracker/watch_list.html"

    def get_queryset(self):
        return WatchItem.objects.filter(user=self.request.user).select_related("share")


class WatchCreateView(LoginRequiredMixin, CreateView):
    """Создание наблюдения (FR-20, FR-21)."""

    template_name = "tracker/watch_form.html"
    form_class = WatchItemForm
    success_url = reverse_lazy("tracker:watch_list")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)


class WatchDeleteView(LoginRequiredMixin, DeleteView):
    """Удаление наблюдения."""

    model = WatchItem
    template_name = "tracker/watch_confirm_delete.html"
    success_url = reverse_lazy("tracker:watch_list")

    def get_queryset(self):
        return WatchItem.objects.filter(user=self.request.user)


class NotificationListView(LoginRequiredMixin, ListView):
    """Список уведомлений (FR-24)."""

    template_name = "tracker/notifications.html"
    paginate_by = 50

    def get_queryset(self):
        return (
            Notification.objects.filter(user=self.request.user)
            .select_related("watch_item__share")
        )


class MarkAllNotificationsReadView(LoginRequiredMixin, View):
    """Отметить все уведомления прочитанными (FR-24)."""

    def post(self, request):
        Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
        return redirect("tracker:notifications")


class PortfolioListView(LoginRequiredMixin, ListView):
    """Список портфелей (FR-25)."""

    template_name = "tracker/portfolio_list.html"

    def get_queryset(self):
        return Portfolio.objects.filter(user=self.request.user)


class PortfolioCreateView(LoginRequiredMixin, CreateView):
    """Создание портфеля (FR-25)."""

    template_name = "tracker/portfolio_form.html"
    form_class = PortfolioForm
    success_url = reverse_lazy("tracker:portfolio_list")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)


class PortfolioDetailView(LoginRequiredMixin, DetailView):
    """Портфель с позициями, стоимостью и P&L (FR-29)."""

    model = Portfolio
    template_name = "tracker/portfolio_detail.html"

    def get_queryset(self):
        return Portfolio.objects.filter(user=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        transactions = list(self.object.transactions.select_related("share").order_by("created_at"))
        positions, realized = calculate_position(transactions)
        shares = Share.objects.in_bulk([sid for sid, (qty, _avg) in positions.items() if qty > 0])

        items = []
        total_value = 0.0
        unrealized_total = 0.0
        for sid, (qty, avg) in sorted(positions.items()):
            if qty <= 0:
                continue
            share = shares[sid]
            current = share.last_price or 0.0
            value = qty * current
            unrealized = (current - avg) * qty
            total_value += value
            unrealized_total += unrealized
            items.append(
                {
                    "share": share,
                    "quantity": qty,
                    "avg_price": avg,
                    "current_price": current,
                    "value": value,
                    "unrealized_pnl": unrealized,
                }
            )

        context.update(
            {
                "items": items,
                "transactions": transactions,
                "realized_pnl": realized,
                "total_value": total_value,
                "unrealized_pnl": unrealized_total,
            }
        )
        return context


class TransactionCreateView(LoginRequiredMixin, CreateView):
    """Операция покупки/продажи (FR-26, FR-27)."""

    template_name = "tracker/transaction_form.html"
    form_class = TransactionForm

    def dispatch(self, request, *args, **kwargs):
        self.portfolio = get_object_or_404(Portfolio, pk=kwargs["pk"], user=request.user)
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["portfolio"] = self.portfolio
        return kwargs

    def form_valid(self, form):
        form.instance.portfolio = self.portfolio
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("tracker:portfolio_detail", kwargs={"pk": self.portfolio.pk})


class TransactionDeleteView(LoginRequiredMixin, DeleteView):
    """Удаление операции (FR-30): позиции пересчитаются автоматически."""

    model = Transaction
    template_name = "tracker/transaction_confirm_delete.html"

    def get_queryset(self):
        return Transaction.objects.filter(portfolio__user=self.request.user)

    def get_success_url(self):
        return reverse_lazy("tracker:portfolio_detail", kwargs={"pk": self.object.portfolio.pk})


class StrategyListView(LoginRequiredMixin, ListView):
    """Список стратегий с эффективностью (FR-38)."""

    template_name = "tracker/strategy_list.html"

    def get_queryset(self):
        return Strategy.objects.filter(user=self.request.user).select_related("share")


class StrategyCreateView(LoginRequiredMixin, CreateView):
    """Создание стратегии (FR-35)."""

    template_name = "tracker/strategy_form.html"
    form_class = StrategyForm
    success_url = reverse_lazy("tracker:strategies")

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)


class StrategyRunView(LoginRequiredMixin, View):
    """Ручной прогон стратегии по текущей цене (FR-39)."""

    def post(self, request, pk):
        strategy = get_object_or_404(Strategy, pk=pk, user=request.user)
        price = strategy.share.last_price
        if price is None:
            messages.warning(
                request, "Текущая цена недоступна — дождитесь фонового обновления цен."
            )
        elif run_strategy(strategy, price):
            messages.success(request, f"Стратегия исполнена по цене {price:.2f}.")
        else:
            messages.info(request, "Условие стратегии не выполнено или лимит сделок исчерпан.")
        return redirect("tracker:strategies")


class StrategyDeleteView(LoginRequiredMixin, DeleteView):
    """Удаление стратегии."""

    model = Strategy
    template_name = "tracker/strategy_confirm_delete.html"
    success_url = reverse_lazy("tracker:strategies")

    def get_queryset(self):
        return Strategy.objects.filter(user=self.request.user)
