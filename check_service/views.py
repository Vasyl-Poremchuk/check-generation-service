from typing import Any

from django.http import FileResponse
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view
from rest_framework.request import Request
from rest_framework.response import Response

from check_generation_service import settings
from check_service.models import Printer, Check
from check_service.serializers import PrinterSerializer, CheckSerializer
from check_service.tasks import generate_pdf


class PrinterViewSet(viewsets.ModelViewSet):
    queryset = Printer.objects.all()
    serializer_class = PrinterSerializer


class CheckViewSet(viewsets.ModelViewSet):
    queryset = Check.objects.all()
    serializer_class = CheckSerializer

    def create(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """
        The method creates new checks.
        """
        order_id = request.data.get("order", {}).get("order_id")
        if not order_id:
            return Response(
                {"message": "Order id is missing."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if Check.objects.filter(order__order_id=order_id).exists():
            return Response(
                {"message": f"Checks for order: {order_id} already exist."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        point_id = request.data.get("order", {}).get("point_id")
        if not point_id:
            return Response(
                {"message": "Point id is missing from the order."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        printers = Printer.objects.filter(point_id=point_id)
        if not printers:
            return Response(
                {
                    "message": f"There are no printers available for point: {point_id}."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        checks = []
        for printer in printers:
            check_data = {
                "printer_id": printer.id,
                "check_type": printer.check_type,
                "order": request.data.get("order"),
            }
            serializer = CheckSerializer(data=check_data)
            serializer.is_valid(raise_exception=True)
            check = serializer.save()
            checks.append(check)

            generate_pdf.delay()

        return Response(
            {"checks": CheckSerializer(checks, many=True).data},
            status=status.HTTP_201_CREATED,
        )

    @action(
        detail=False,
        methods=["get"],
        url_path=r"print-checks/(?P<api_key>[\w-]+)",
        url_name="print-checks",
    )
    def print_checks(self, request: Request, api_key: str) -> Response:
        """
        The method changes check status from `RENDERED` to `PRINTED`.
        """
        try:
            printer = Printer.objects.get(api_key=api_key)
        except Printer.DoesNotExist:
            return Response(
                {"message": "There are no available printers."},
                status=status.HTTP_404_NOT_FOUND,
            )

        checks = printer.checks.filter(status=Check.StatusChoices.RENDERED)

        if not checks:
            return Response(
                {
                    "message": f"There are no checks available for the printer: {printer.id}."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        for check in checks:
            check.status = Check.StatusChoices.PRINTED
            check.save()

        serializer = self.get_serializer(checks, many=True)

        return Response(serializer.data)


@api_view(["GET"])
def download_check(request: Request, check_id: int) -> Response | FileResponse:
    """
    The method returns a printed check from the media root.
    """
    check = Check.objects.get(id=check_id)

    if check.status != Check.StatusChoices.PRINTED:
        return Response(
            {"message": f"Check: {check_id} is not available for download."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    path = f"pdf/{check.order['order_id']}_{check.check_type}.pdf"
    filepath = settings.MEDIA_ROOT / path

    if not filepath.exists():
        return Response(
            {"message": "There is no available check for download."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    response = FileResponse(open(filepath, "rb"))
    response["Content-Disposition"] = f"inline; filename={filepath.name}"

    return response
