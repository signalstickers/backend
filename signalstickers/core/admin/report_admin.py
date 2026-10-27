from core.models import Report, ReportStatus
from django.contrib import admin
from django.contrib.admin.options import HttpResponseRedirect, csrf_protect_m
from django.urls import reverse
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

    # POST button name -> ReportStatus name
    _STATUS_BY_POST_KEY = {
        "_agree": ReportStatus.AGREED.name,
        "_disagree": ReportStatus.DISAGREED.name,
    }
    _REVIEW_KEYS = ("_agree", "_disagree")

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

    @staticmethod
    def _status_from_post(post):
        for post_key, status in ReportAdmin._STATUS_BY_POST_KEY.items():
            if post_key in post:
                return status
        return None

    def _review_single(self, request, object_id, form_url, extra_context):
        # Save the form with the posted status
        posted_data = request.POST.copy()
        status = self._status_from_post(request.POST)
        if status is not None:
            posted_data["status"] = status

        request.POST = posted_data
        # Save all fields
        super().changeform_view(
            request, object_id, form_url, extra_context=extra_context
        )

        # Redirect back to the report list
        return HttpResponseRedirect(reverse("admin:core_report_changelist"))

    @csrf_protect_m
    def changeform_view(self, request, object_id=None, form_url="", extra_context=None):
        if request.method == "POST":
            if any(key in self._REVIEW_KEYS for key in request.POST.keys()):
                return self._review_single(request, object_id, form_url, extra_context)

        return admin.ModelAdmin.changeform_view(
            self,
            request,
            object_id=object_id,
            form_url=form_url,
            extra_context=extra_context,
        )
