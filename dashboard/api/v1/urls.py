from rest_framework.routers import DefaultRouter

from dashboard.api.v1.viewsets import (
    NotificationViewSet,
    PortfolioOperationViewSet,
    PortfolioViewSet,
    PriceAlertViewSet,
    PriceHistoryViewSet,
    ShareViewSet,
    StrategyTradeViewSet,
    StrategyViewSet,
    WatchlistItemViewSet,
)

router = DefaultRouter()
router.register("shares", ShareViewSet, basename="share")
router.register("watchlist", WatchlistItemViewSet, basename="watchlist")
router.register("alerts", PriceAlertViewSet, basename="pricealert")
router.register("notifications", NotificationViewSet, basename="notification")
router.register("portfolios", PortfolioViewSet, basename="portfolio")
router.register(
    "portfolio-operations", PortfolioOperationViewSet, basename="portfoliooperation"
)
router.register("price-history", PriceHistoryViewSet, basename="pricehistory")
router.register("strategies", StrategyViewSet, basename="strategy")
router.register("strategy-trades", StrategyTradeViewSet, basename="strategytrade")

urlpatterns = router.urls
