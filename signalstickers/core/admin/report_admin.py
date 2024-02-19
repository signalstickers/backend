from core.models import Report, ReportStatus
from django.contrib import admin
from django.utils.safestring import mark_safe


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):

    search_fields = ("pack__title",)
    list_display = (
        "date",
        "_status",
        "get_pack_title",
        "get_pack_id",
    )

    readonly_fields = ("pack", "content")

    fieldsets = (
        ("User report", {"fields": ("pack", "content")}),
        ("Decision", {"fields": ("status",)}),
    )

    @admin.display(description="Status")
    def _status(self, obj):
        if obj.status == ReportStatus.TO_PROCESS.name:
            return mark_safe('<b style="color:red">To process</b>')  # nosec
        return ReportStatus[obj.status].value

    @admin.display(description="Pack title")
    def get_pack_title(self, obj):
        return obj.pack.title

    @admin.display(description="Pack ID")
    def get_pack_id(self, obj):
        return obj.pack.pack_id
