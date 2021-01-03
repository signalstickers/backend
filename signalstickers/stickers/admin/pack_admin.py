from django.contrib import admin, messages
from django.utils.html import escape
from django.utils.safestring import mark_safe
from stickers.models import Pack, PackStatus
from stickers.utils import get_pack_from_signal


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
            return mark_safe(
                f'<a target="_blank" href="https://signalstickers.com/pack/{escape(obj.pack_id)}">View</a>'
            )
        return mark_safe(
            f'<a target="_blank" href="https://signalstickers.com/pack/{escape(obj.pack_id)}?key={escape(obj.pack_key)}">View</a>'
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

    # def changelist_view(self, request, *args, **kwargs):
    #     packs_to_review = Pack.objects.filter(status="IN_REVIEW").count()
    #     if packs_to_review:
    #         messages.add_message(
    #             request,
    #             messages.WARNING,
    #             mark_safe(
    #                 f"<b>{packs_to_review} packs are waiting for review.</b> "
    #                 "<a href='?status__exact=IN_REVIEW'>Review</a>"
    #             ),
    #         )

    #     return super().changelist_view(request, *args, **kwargs)

    #
    # Edit view
    #

    # Custom view to display stickers images
    change_form_template = "admin/change_form_pack.html"

    fieldsets = (
        ("Pack info", {"fields": ("pack_id", "pack_key", "title", "author")}),
        ("Metadata", {"fields": ("source", "nsfw", "original", "tags")}),
        ("Animation", {"fields": ("animated_detected", "animated_mode", "animated")}),
        ("Review", {"fields": ("submitter_comments", "status", "status_comments")}),
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
                }
            }
        )
        return super().get_form(request, obj, **kwargs)

