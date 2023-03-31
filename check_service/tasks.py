import os

from celery import shared_task
from django.template.loader import render_to_string

from check_generation_service import settings
from check_service.models import Check


@shared_task
def generate_pdf() -> None:
    """
    The task converts a html page to a pdf page.
    """
    checks = Check.objects.all()

    for check in checks:
        order_id = check.order["order_id"]
        check_type = check.check_type
        dishes = check.order["dishes"]
        filename = f"{order_id}_{check_type}.pdf"
        filepath = os.path.join(settings.MEDIA_ROOT, "pdf", filename)
        total_amount_due = sum(dish["total_price"] for dish in dishes)

        html = render_to_string(
            "check.html",
            {"check": check, "total_amount_due": total_amount_due},
        )
        cmd = f"wkhtmltopdf - - > {filepath}"
        process = os.popen(cmd, "w")
        process.write(html)
        process.close()

        check.pdf_file.name = os.path.join("pdf", filename)
        check.status = Check.StatusChoices.RENDERED
        check.save()
