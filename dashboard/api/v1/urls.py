from rest_framework.routers import DefaultRouter

from dashboard.api.v1.viewsets import ShareViewSet

router = DefaultRouter()
router.register("shares", ShareViewSet, basename="share")

urlpatterns = router.urls
