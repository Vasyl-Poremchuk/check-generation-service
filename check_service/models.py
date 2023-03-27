from django.db import models


class CheckTypeChoices(models.TextChoices):
    KITCHEN = "kitchen"
    CLIENT = "client"


class Printer(models.Model):
    name = models.CharField(max_length=70)
    api_key = models.CharField(max_length=70, unique=True)
    check_type = models.CharField(
        max_length=7, choices=CheckTypeChoices.choices
    )
    point_id = models.IntegerField()

    def __str__(self) -> str:
        """
        The method returns a string representation
        of an instance of the `Printer` class.
        """
        return f"Printer name: {self.name}. Check type: {self.check_type}."


class Check(models.Model):
    class StatusChoices(models.TextChoices):
        NEW = "new"
        RENDERED = "rendered"
        PRINTED = "printed"

    printer_id = models.ForeignKey(
        Printer, on_delete=models.CASCADE, related_name="checks"
    )
    check_type = models.CharField(
        max_length=7, choices=CheckTypeChoices.choices
    )
    order = models.JSONField()
    status = models.CharField(
        max_length=8, choices=StatusChoices.choices, default=StatusChoices.NEW
    )
    pdf_file = models.FileField(upload_to="pdf/", null=True, blank=True)

    def __str__(self) -> str:
        """
        The method returns a string representation
        of an instance of the `Check` class.
        """
        return (
            f"Printer id: {self.printer_id}. "
            f"Check type: {self.check_type}. Status: {self.status}."
        )
