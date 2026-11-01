from django.urls import path

from . import views

app_name = "tracker"

urlpatterns = [
    path("watch/", views.WatchListView.as_view(), name="watch_list"),
    path("watch/create/", views.WatchCreateView.as_view(), name="watch_create"),
    path("watch/<int:pk>/delete/", views.WatchDeleteView.as_view(), name="watch_delete"),
    path("notifications/", views.NotificationListView.as_view(), name="notifications"),
    path(
        "notifications/read-all/",
        views.MarkAllNotificationsReadView.as_view(),
        name="notifications_read_all",
    ),
    path("portfolios/", views.PortfolioListView.as_view(), name="portfolio_list"),
    path("portfolios/create/", views.PortfolioCreateView.as_view(), name="portfolio_create"),
    path("portfolios/<int:pk>/", views.PortfolioDetailView.as_view(), name="portfolio_detail"),
    path(
        "portfolios/<int:pk>/transactions/create/",
        views.TransactionCreateView.as_view(),
        name="transaction_create",
    ),
    path(
        "transactions/<int:pk>/delete/",
        views.TransactionDeleteView.as_view(),
        name="transaction_delete",
    ),
    path("strategies/", views.StrategyListView.as_view(), name="strategies"),
    path("strategies/create/", views.StrategyCreateView.as_view(), name="strategy_create"),
    path("strategies/<int:pk>/run/", views.StrategyRunView.as_view(), name="strategy_run"),
    path("strategies/<int:pk>/delete/", views.StrategyDeleteView.as_view(), name="strategy_delete"),
]
