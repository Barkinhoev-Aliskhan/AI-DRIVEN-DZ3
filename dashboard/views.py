from datetime import timedelta

from django.contrib.auth.mixins import UserPassesTestMixin
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView, DeleteView, ListView, UpdateView, View

from .forms import ShareModelForm
from .models import Share
from .services.graph import get_graph, get_history_graph
from tracker.logic import price_change


class IsUserAuthenticatedMixin(UserPassesTestMixin):
    """Разрешает доступ только аутентифицированным пользователям."""

    def test_func(self):
        return self.request.user.is_authenticated

    @staticmethod
    def handle_no_permission():
        return redirect("dashboard:index")


class ShareListView(ListView):
    """Список акций с пагинацией."""

    model = Share
    template_name = "dashboard/list.html"
    paginate_by = 100
    ordering = ["name"]


class ShareDetailView(View):
    """Детальная страница акции с графиком цены."""

    @staticmethod
    def get(request, pk):
        share = get_object_or_404(Share, id=pk)
        return render(
            request,
            "dashboard/detail.html",
            {"plot_div": get_graph(share), "share": share},
        )


class ShareCreateView(IsUserAuthenticatedMixin, CreateView):
    """Добавление инструмента."""

    template_name = "dashboard/create.html"
    form_class = ShareModelForm
    success_url = reverse_lazy("dashboard:index")


class ShareUpdateView(IsUserAuthenticatedMixin, UpdateView):
    """Редактирование инструмента."""

    model = Share
    template_name = "dashboard/create.html"
    form_class = ShareModelForm
    success_url = reverse_lazy("dashboard:index")


class ShareDeleteView(IsUserAuthenticatedMixin, DeleteView):
    """Удаление инструмента."""

    model = Share
    template_name = "dashboard/delete.html"
    success_url = reverse_lazy("dashboard:index")


class PriceHistoryView(View):
    """История изменения цен за выбранный период."""

    PERIODS = (7, 30, 90, 180)

    @staticmethod
    def get(request):
        shares = Share.objects.all().order_by("name")
        try:
            period = int(request.GET.get("period", "30"))
        except ValueError:
            period = 30
        if period not in PriceHistoryView.PERIODS:
            period = 30

        share_id = request.GET.get("share")
        history, change, plot_div = None, None, ""
        if share_id:
            share = get_object_or_404(Share, id=share_id)
            since = timezone.now() - timedelta(days=period)
            history = share.price_history.filter(recorded_at__gte=since).order_by("recorded_at")
            if history.exists():
                change = price_change(history.first().price, history.last().price)
                plot_div = get_history_graph(history)

        return render(
            request,
            "dashboard/history.html",
            {
                "shares": shares,
                "selected_share_id": int(share_id) if share_id else None,
                "period": period,
                "history": history,
                "change": change,
                "plot_div": plot_div,
            },
        )
