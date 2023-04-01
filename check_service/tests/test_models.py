import json

from django.test import TestCase

from check_service.models import Printer, Check


class ModelsTests(TestCase):
    def test_printer_str(self) -> None:
        printer = Printer.objects.create(
            name="HP ScanJet Pro 2000",
            api_key="bcc65a51-953c-4538-8c84-662868ab4edc",
            check_type="client",
            point_id=1,
        )

        self.assertEqual(
            str(printer),
            f"Printer name: {printer.name}. Check type: {printer.check_type}.",
        )

    def test_check_str(self) -> None:
        printer = Printer.objects.create(
            name="HP ScanJet Pro 2000",
            api_key="bcc65a51-953c-4538-8c84-662868ab4edc",
            check_type="client",
            point_id=1,
        )
        order = {
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
        order_json = json.dumps(order)
        check = Check.objects.create(
            printer_id=printer,
            check_type=printer.check_type,
            order=order_json,
        )

        self.assertEqual(
            str(check),
            f"Printer id: {printer}. Check type: {check.check_type}. Status: {check.status}.",
        )
