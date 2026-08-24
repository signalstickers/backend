import logging
from urllib.parse import parse_qsl, urlencode

from core.admin.bulk_review import LAST_PACK, parse_next_ids, redirect_to_next_pack
from core.models import Pack, PackStatus
from core.notifications import NotificationPriority, notify
from core.utils import admin_url
from django.contrib import admin
from django.contrib.admin.options import HttpResponseRedirect, csrf_protect_m
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.html import format_html
from django.utils.safestring import mark_safe

logger = logging.getLogger("main")


@admin.register(Pack)
class PackAdmin(admin.ModelAdmin):

    #
    # Computed fields
    #

    def _status(self, obj):
        if obj.status == PackStatus.IN_REVIEW.name:
            return mark_safe('<b style="color:red">To review</b>')  # nosec
        if obj.status == PackStatus.ESCALATED.name:
            return mark_safe('<b style="color:blue">Escalated</b>')  # nosec
        return PackStatus[obj.status].value

    def _view(self, obj):
        if obj.status == PackStatus.ONLINE.name:
            return format_html(
                '<a target="_blank" href="https://signalstickers.org/pack/{}">View</a>',
                obj.pack_id,
            )
        return format_html(
            '<a target="_blank" href="https://signalstickers.org/pack/{}?key={}">View</a>',
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
        "editorschoice",
        "animated",
        "_view",
    )
    search_fields = ("title", "pack_id", "pack_key", "tags__name")
    list_filter = ("status", "original", "nsfw", "animated", "editorschoice")

    #
    # Edit view
    #

    # Custom view to display stickers images
    change_form_template = "admin/change_form_pack.html"

    def _ai_review_statuses(self, obj):

        if not obj.ai_review:
            return None

        tpl = render_to_string("admin/ai_review_partial.html", {"pack": obj})

        return mark_safe(tpl)  # nosec

    _ai_review_statuses.short_description = "Hints"

    def _ai_review_comments(self, obj):
        return obj.ai_review.review_comment

    _ai_review_comments.short_description = "Comments"

    fieldsets = (
        ("Pack info", {"fields": ("pack_id", "pack_key", "title", "author")}),
        (
            "Metadata",
            {"fields": ("source", "nsfw", "original", "tags", "editorschoice")},
        ),
        ("Animation", {"fields": ("animated_detected", "animated_mode", "animated")}),
        (
            "Review",
            {"fields": ("submitter_comments", "status", "status_comments")},
        ),
        (
            "Hints from AI review",
            {"fields": ("_ai_review_statuses", "_ai_review_comments")},
        ),
    )

    autocomplete_fields = ("tags",)
    readonly_fields = (
        "title",
        "author",
        "animated_detected",
        "animated",
        "submitter_comments",
        "_ai_review_statuses",
        "_ai_review_comments",
    )
    actions = ("bulk_review_packs",)

    # POST button name -> PackStatus name, for the single and continue review flows
    _STATUS_BY_POST_KEY = {
        "_approve": PackStatus.ONLINE.name,
        "_refuse": PackStatus.REFUSED.name,
        "_escalate": PackStatus.ESCALATED.name,
        "_approve_continue": PackStatus.ONLINE.name,
        "_refuse_continue": PackStatus.REFUSED.name,
        "_escalate_continue": PackStatus.ESCALATED.name,
    }
    _SINGLE_REVIEW_KEYS = ("_approve", "_refuse", "_escalate")

    @staticmethod
    def _status_from_post(post):
        for post_key, status in PackAdmin._STATUS_BY_POST_KEY.items():
            if post_key in post:
                return status
        return None

    @staticmethod
    def _notify_escalation(pack, username):
        logger.info("Pack %s (%s) escalated", pack.title, pack.pack_id)
        notify(
            "signalstickers-admin",
            "Escalated pack",
            f"Pack '{pack.title}' escalated by {username}, please review",
            priority=NotificationPriority.HIGH,
            tags=["arrow_heading_up"],
            click_url=admin_url(),
        )

    @staticmethod
    def _redirect_after_review(request):
        remaining_packs = Pack.objects.in_review_count()
        url = reverse("admin:core_pack_changelist")
        if remaining_packs and request.GET.get("_changelist_filters"):
            query_params = dict(parse_qsl(request.GET["_changelist_filters"]))
            params = []
            for key, value in query_params.items():
                params.append(f"{key}={value}")
            url = f"{reverse('admin:core_pack_changelist')}?{'&'.join(params)}"
        return HttpResponseRedirect(url)

    # Add help texts for some fields
    def get_form(self, request, obj=None, **kwargs):  # pylint: disable=arguments-differ
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
        form = super().get_form(request, obj, **kwargs)

        if not request.user.is_superuser:
            form.base_fields["pack_id"].disabled = True
            form.base_fields["pack_key"].disabled = True

        return form

    # customs actions
    @admin.action(description="Start a bulk review session")
    def bulk_review_packs(self, request, queryset):
        ordered_queryset = queryset.order_by("id")

        # If no queryset == no pack selected in the list, so see if there's another action to do
        if not ordered_queryset:
            if "-2" in request.POST["_selected_action"]:
                ordered_queryset = Pack.objects.in_review().order_by("id")
            elif "-3" in request.POST["_selected_action"]:
                ordered_queryset = Pack.objects.escalated().order_by("id")

        # Add the next pack ids to the GET parameters
        object_id = str(ordered_queryset.first().id)
        pack_ids = [
            str(pack_id) for pack_id in ordered_queryset.values_list("id", flat=True)
        ]
        pack_ids.remove(object_id)  # remove current object from the list

        return redirect_to_next_pack(object_id, pack_ids, urlencode(request.GET))

    def _review_single(self, request, object_id, form_url, extra_context):
        # Classic pack review: save the form with the posted status, then stop
        posted_data = request.POST.copy()
        status = self._status_from_post(request.POST)
        if status is not None:
            posted_data["status"] = status

        previous_status = Pack.objects.get(pk=object_id).status
        request.POST = posted_data
        # Save all fields
        super().changeform_view(
            request, object_id, form_url, extra_context=extra_context
        )

        if "_escalate" in request.POST and previous_status != PackStatus.ESCALATED.name:
            self._notify_escalation(
                Pack.objects.get(pk=object_id), request.user.username
            )

        # Once the pack is saved and status changed to approved
        # redirect to previous page with correct url params
        return self._redirect_after_review(request)

    def _review_continue(self, request, object_id, form_url, extra_context):
        # Bulk session: save the form with the posted status, then move on
        posted_data = request.POST.copy()
        status = self._status_from_post(request.POST)
        if status is not None:
            posted_data["status"] = status

        previous_pack = Pack.objects.get(pk=object_id)
        request.POST = posted_data
        # Save all fields
        super().changeform_view(
            request, object_id, form_url, extra_context=extra_context
        )

        if (
            "_escalate_continue" in request.POST
            and previous_pack.status != PackStatus.ESCALATED.name
        ):
            self._notify_escalation(previous_pack, request.user.username)

        # Redirect to the next pack
        remaining_ids = parse_next_ids(request.POST.get("_bulkreview_next"))
        if not remaining_ids:
            return self._redirect_after_review(request)
        return redirect_to_next_pack(
            remaining_ids[0], remaining_ids[1:], request.GET.get("_changelist_filters")
        )

    @csrf_protect_m
    def changeform_view(self, request, object_id=None, form_url="", extra_context=None):
        if request.method == "POST":
            if any(key in self._SINGLE_REVIEW_KEYS for key in request.POST.keys()):
                return self._review_single(request, object_id, form_url, extra_context)
            if any("_continue" in key for key in request.POST.keys()):
                return self._review_continue(
                    request, object_id, form_url, extra_context
                )

        if request.method == "GET" and "_bulkreview_next" in request.GET:
            # In case of a bulk action, get the next pack ids and add it to context
            extra_context = {
                "bulk_pack_ids": request.GET.get("_bulkreview_next") or LAST_PACK
            }

        return admin.ModelAdmin.changeform_view(
            self,
            request,
            object_id=object_id,
            form_url=form_url,
            extra_context=extra_context,
        )
