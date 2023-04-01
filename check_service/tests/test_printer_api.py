from django.test import TestCase
from django.urls import reverse
from rest_framework import status

from rest_framework.test import APIClient

from check_service.models import Printer
from check_service.serializers import PrinterSerializer


PRINTER_LIST_URL = reverse("check_service:printer-list")


class PrinterApiTests(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.first_printer = Printer.objects.create(
            name="HP ScanJet Pro 2000",
            api_key="bcc65a51-953c-4538-8c84-662868ab4edc",
            check_type="client",
            point_id=1,
        )
        self.second_printer = Printer.objects.create(
            name="HP ScanJet Pro 3000",
            api_key="6f65be59-89fe-4c7e-be12-c0b30945aee7",
            check_type="kitchen",
            point_id=1,
        )

    def test_list_printers(self) -> None:
        response = self.client.get(PRINTER_LIST_URL)
        printers = Printer.objects.all()
        serializer = PrinterSerializer(printers, many=True)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)
        self.assertEqual(len(response.data), 2)

    def test_create_printer(self) -> None:
        payload = {
            "name": "HP ScanJet Enterprise Flow N7000",
            "api_key": "5a516cfd-7e8b-43ec-b199-20bb15f7da94",
            "check_type": "client",
            "point_id": 2,
        }
        response = self.client.post(PRINTER_LIST_URL, payload)
        printer = Printer.objects.get(name="HP ScanJet Enterprise Flow N7000")
        serializer = PrinterSerializer(printer)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data, serializer.data)

    def test_retrieve_printer(self) -> None:
        printer_detail_url = reverse(
            "check_service:printer-detail",
            kwargs={"pk": self.first_printer.pk},
        )
        response = self.client.get(printer_detail_url)
        printer = Printer.objects.get(pk=self.first_printer.pk)
        serializer = PrinterSerializer(printer)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)

    def test_update_printer(self) -> None:
        printer_detail_url = reverse(
            "check_service:printer-detail",
            kwargs={"pk": self.second_printer.pk},
        )
        payload = {
            "name": "HP LaserJet Pro 4001ne",
            "api_key": "fd7547d2-00c3-44aa-9469-57b7bce87731",
            "check_type": "kitchen",
            "point_id": 3,
        }
        response = self.client.put(printer_detail_url, payload)
        printer = Printer.objects.get(pk=self.second_printer.pk)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(printer.name, payload["name"])
        self.assertEqual(printer.api_key, payload["api_key"])
        self.assertEqual(printer.point_id, payload["point_id"])

    def test_partial_update_printer(self) -> None:
        printer_detail_url = reverse(
            "check_service:printer-detail",
            kwargs={"pk": self.first_printer.pk},
        )
        payload = {"name": "HP LaserJet Pro 4001dw"}
        response = self.client.patch(printer_detail_url, payload)
        printer = Printer.objects.get(pk=self.first_printer.pk)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(printer.name, payload["name"])

    def test_delete_printer(self) -> None:
        printer_detail_url = reverse(
            "check_service:printer-detail",
            kwargs={"pk": self.second_printer.pk},
        )
        response = self.client.delete(printer_detail_url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(
            Printer.objects.filter(pk=self.second_printer.pk).exists()
        )
