from django.urls import include, path
from rest_framework import routers

from check_service.views import PrinterViewSet, CheckViewSet, download_check

router = routers.DefaultRouter()
router.register("printers", PrinterViewSet)
router.register("checks", CheckViewSet)

urlpatterns = [
    path("", include(router.urls)),
    path(
        "download-checks/<int:check_id>/",
        download_check,
        name="download-check",
    ),
]

app_name = "check-service"
