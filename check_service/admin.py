from django.contrib import admin

from check_service.models import Printer, Check


@admin.register(Printer)
class PrinterAdmin(admin.ModelAdmin):
    search_fields = ("name",)
    list_filter = ("name", "check_type")


@admin.register(Check)
class CheckAdmin(admin.ModelAdmin):
    list_filter = ("printer_id", "check_type", "status")
