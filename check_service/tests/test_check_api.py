import json
from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse
from rest_framework import status

from rest_framework.test import APIClient

from check_service.models import Printer, Check
from check_service.serializers import CheckSerializer


CHECK_LIST_URL = reverse("check_service:check-list")


class CheckApiTests(TestCase):
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
        self.order = {
            "order_id": 101,
            "client_name": "Maria Hernandez",
            "point_id": 1,
            "dishes": [
                {
                    "name": "Pizza",
                    "amount": 2,
                    "price_one_dish": 5.7,
                    "total_price": 11.4,
                },
                {
                    "name": "Burger",
                    "amount": 2,
                    "price_one_dish": 4.5,
                    "total_price": 9,
                },
            ],
        }
        self.order_json = json.dumps(self.order)
        self.first_check = Check.objects.create(
            printer_id=self.first_printer,
            check_type=self.first_printer.check_type,
            order=self.order_json,
        )
        self.second_check = Check.objects.create(
            printer_id=self.second_printer,
            check_type=self.second_printer.check_type,
            order=self.order_json,
        )

    def test_list_checks(self) -> None:
        response = self.client.get(CHECK_LIST_URL)
        checks = Check.objects.all()
        serializer = CheckSerializer(checks, many=True)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)
        self.assertEqual(len(response.data), 2)

    def test_create_check_missing_order_id(self) -> None:
        payload = {
            "printer_id": 1,
            "check_type": "kitchen",
            "order": {
                "client_name": "Maria Hernandez",
                "point_id": 1,
                "dishes": [
                    {
                        "name": "Pizza",
                        "amount": 2,
                        "price_one_dish": 5.7,
                        "total_price": 11.4,
                    },
                    {
                        "name": "Burger",
                        "amount": 2,
                        "price_one_dish": 4.5,
                        "total_price": 9,
                    },
                ],
            },
        }
        response = self.client.post(CHECK_LIST_URL, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["message"], "Order id is missing.")
        self.assertEqual(Check.objects.count(), 2)

    def test_create_check_missing_point_id(self) -> None:
        payload = {
            "printer_id": 1,
            "check_type": "kitchen",
            "order": {
                "order_id": 101,
                "client_name": "Maria Hernandez",
                "dishes": [
                    {
                        "name": "Pizza",
                        "amount": 2,
                        "price_one_dish": 5.7,
                        "total_price": 11.4,
                    },
                    {
                        "name": "Burger",
                        "amount": 2,
                        "price_one_dish": 4.5,
                        "total_price": 9,
                    },
                ],
            },
        }
        response = self.client.post(CHECK_LIST_URL, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data["message"], "Point id is missing from the order."
        )
        self.assertEqual(Check.objects.count(), 2)

    def test_create_check_no_printer_available(self) -> None:
        payload = {
            "printer_id": 7,
            "check_type": "kitchen",
            "order": {
                "order_id": 127,
                "client_name": "Maria Hernandez",
                "point_id": 7,
                "dishes": [
                    {
                        "name": "Pizza",
                        "amount": 2,
                        "price_one_dish": 5.7,
                        "total_price": 11.4,
                    },
                ],
            },
        }
        response = self.client.post(CHECK_LIST_URL, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data["message"],
            f"There are no printers available for point: {payload['order']['point_id']}.",
        )

    def test_create_check(self) -> None:
        payload = {
            "printer_id": 1,
            "check_type": "kitchen",
            "order": {
                "order_id": 127,
                "client_name": "Maria Hernandez",
                "point_id": 1,
                "dishes": [
                    {
                        "name": "Pizza",
                        "amount": 2,
                        "price_one_dish": 5.7,
                        "total_price": 11.4,
                    },
                ],
            },
        }
        with patch(
            "check_service.tasks.generate_pdf.delay"
        ) as mock_generate_pdf:
            response = self.client.post(CHECK_LIST_URL, payload, format="json")

            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            self.assertEqual(mock_generate_pdf.call_count, 2)

    def test_retrieve_check(self) -> None:
        check_detail_url = reverse(
            "check_service:check-detail", kwargs={"pk": self.first_check.pk}
        )
        response = self.client.get(check_detail_url)
        check = Check.objects.get(pk=self.first_check.pk)
        serializer = CheckSerializer(check)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)

    def test_update_check(self) -> None:
        check_detail_url = reverse(
            "check_service:check-detail", kwargs={"pk": self.second_check.pk}
        )
        updated_order = {
            "order_id": 101,
            "client_name": "Henry Davis",
            "point_id": 1,
            "dishes": [
                {
                    "name": "Salsa chicken",
                    "amount": 5,
                    "price_onde_dish": 3.3,
                    "total_price": 16.5,
                }
            ],
        }
        payload = {
            "printer_id": self.second_printer.pk,
            "check_type": self.second_printer.check_type,
            "order": updated_order,
        }
        response = self.client.put(check_detail_url, payload, format="json")
        check = Check.objects.get(pk=self.second_check.pk)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(check.printer_id.pk, payload["printer_id"])
        self.assertEqual(check.check_type, payload["check_type"])
        self.assertEqual(check.order, payload["order"])

    def test_partial_update_check(self) -> None:
        check_detail_url = reverse(
            "check_service:check-detail", kwargs={"pk": self.first_check.pk}
        )
        payload = {"order": {"client_name": "Jane Miller"}}
        response = self.client.patch(check_detail_url, payload, format="json")
        check = Check.objects.get(pk=self.first_check.pk)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            check.order["client_name"], payload["order"]["client_name"]
        )

    def test_delete_check(self) -> None:
        check_detail_url = reverse(
            "check_service:check-detail", kwargs={"pk": self.second_check.pk}
        )
        response = self.client.delete(check_detail_url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(
            Check.objects.filter(pk=self.second_check.pk).exists()
        )
