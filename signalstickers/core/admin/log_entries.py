from django.contrib import admin
from django.contrib.admin.models import DELETION, LogEntry
from django.urls import NoReverseMatch, reverse
from django.utils.html import escape
from django.utils.safestring import mark_safe


@admin.register(LogEntry)
class LogEntryAdmin(admin.ModelAdmin):

    date_hierarchy = "action_time"
    list_filter = ("user", "content_type", "action_flag")
    search_fields = ("object_repr", "change_message")

    list_display = [
        "action_time",
        "user",
        "content_type",
        "object_link",
        "action_flag_",
        "change_message",
    ]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def action_flag_(self, obj):
        flags = {1: "Addition", 2: "Changed", 3: "Deleted"}
        return flags[obj.action_flag]

    def object_link(self, obj):
        if obj.action_flag == DELETION:
            link = escape(obj.object_repr)
        else:
            content_type = obj.content_type
            try:
                reverse_url = reverse(
                    f"admin:{content_type.app_label}_{content_type.model}_change",
                    args=[obj.object_id],
                )
                obj_repr = escape(obj.object_repr)
                link = mark_safe(f'<a href="{reverse_url}">{obj_repr}</a>')  # nosec
            except NoReverseMatch:
                link = "N/A"
        return link

    object_link.allow_tags = True
    object_link.admin_order_field = "object_repr"
    object_link.short_description = "object"
