from apps.stickers.models import Pack, PackStatus
from apps.stickers.utils import get_pack_from_signal
from django.contrib import admin, messages
from django.utils.html import format_html
from django.utils.safestring import mark_safe


@admin.register(Pack)
class PackAdmin(admin.ModelAdmin):

    #
    # Computed fields
    #

    def _status(self, obj):
        if obj.status == PackStatus.IN_REVIEW.name:
            return mark_safe('<b style="color:red">To review</b>')
        return PackStatus[obj.status].value

    def _view(self, obj):
        if obj.status == PackStatus.ONLINE.name:
            return format_html(
                '<a target="_blank" href="https://signalstickers.com/pack/{}">View</a>',
                obj.pack_id,
            )
        return format_html(
            '<a target="_blank" href="https://signalstickers.com/pack/{}?key={}">View</a>',
            obj.pack_id,
            obj.pack_key,
        )

    #
    # List view
    #

    list_display = (
        "id",
        "title",
        "_status",
        "pack_id",
        "pack_key",
        "original",
        "nsfw",
        "animated",
        "_view",
    )
    search_fields = ("title", "pack_id", "pack_key", "tags__name")
    list_filter = ("status", "original", "nsfw", "animated")

    #
    # Edit view
    #

    # Custom view to display stickers images
    change_form_template = "admin/change_form_pack.html"

    fieldsets = (
        ("Pack info", {"fields": ("pack_id", "pack_key", "title", "author")}),
        ("Metadata", {"fields": ("source", "nsfw", "original", "tags")}),
        ("Animation", {"fields": ("animated_detected", "animated_mode", "animated")}),
        (
            "Review",
            {"fields": ("submitter_comments", "status", "status_comments", "tweeted")},
        ),
    )
    autocomplete_fields = ("tags",)
    readonly_fields = (
        "title",
        "author",
        "animated_detected",
        "animated",
        "submitter_comments",
    )

    # Add help texts for some fields
    def get_form(self, request, obj=None, **kwargs):
        kwargs.update(
            {
                "help_texts": {
                    "title": "This value in set in the pack, and cannot be changed.",
                    "author": "This value in set in the pack, and cannot be changed.",
                    "animated_detected": "If true, animated stickers have been detected in this pack.",
                    "animated_mode": "Use the auto-detection, or force a animated status if the detection is wrong.",
                    "animated": "This is the final animated status that will be displayed to users.",
                    "submitter_comments": "Users can leave comments when the submit a pack.",
                    "status_comments": "If needed, explain here why the pack has been refused, or almost refused.",
                    "tweeted": "If this checkbox is checked and you uncheck it, the pack will be tweeted again. If the pack is new, check this box to prevent it from being tweeted.",
                }
            }
        )
        return super().get_form(request, obj, **kwargs)
