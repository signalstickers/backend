from urllib.parse import parse_qsl, urlencode

from core.models import Pack, PackStatus
from django.contrib import admin
from django.contrib.admin.options import HttpResponseRedirect, csrf_protect_m, unquote
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.html import format_html
from django.utils.safestring import mark_safe


@admin.register(Pack)
class PackAdmin(admin.ModelAdmin):

    #
    # Computed fields
    #

    def _status(self, obj):
        if obj.status == PackStatus.IN_REVIEW.name:
            return mark_safe('<b style="color:red">To review</b>')  # nosec
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

    fieldsets = (
        ("Pack info", {"fields": ("pack_id", "pack_key", "title", "author")}),
        (
            "Metadata",
            {"fields": ("source", "nsfw", "original", "tags", "editorschoice")},
        ),
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
    actions = ("bulk_review_packs",)

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
                    "tweeted": "If this checkbox is checked and you uncheck it, the pack will be tweeted again. If the pack is new, check this box to prevent it from being tweeted.",
                }
            }
        )
        return super().get_form(request, obj, **kwargs)

    # customs actions
    @admin.action(description="Start a bulk review session")
    def bulk_review_packs(self, request, queryset):
        # Add the next pack ids to the GET parameters
        ordered_queryset = queryset.order_by("id")
        object_id = str(ordered_queryset.first().id)
        pack_ids = [
            str(pack_id) for pack_id in ordered_queryset.values_list("id", flat=True)
        ]
        pack_ids.remove(object_id)  # remove current object from the list

        # create the GET parameters
        params_dict = {
            "_changelist_filters": urlencode(request.GET),
            "_bulkreview_next": ",".join(pack_ids),
        }
        params = urlencode(params_dict)

        return redirect(
            reverse("admin:core_pack_change", kwargs={"object_id": object_id})
            + f"?{params}"
        )

    @csrf_protect_m
    def changeform_view(self, request, object_id=None, form_url="", extra_context=None):
        # Classic pack we need to approve automatically
        if request.method == "POST" and any(
            key in ["_approve", "_refuse"] for key in request.POST.keys()
        ):
            # Save all fields
            super().changeform_view(
                request, object_id, form_url, extra_context=extra_context
            )
            pack = self.get_object(request, unquote(object_id))
            if "_approve" in request.POST:
                pack.approve()
            elif "_refuse" in request.POST:
                pack.refuse()

            # Once the pack is saved and status changed to approved
            # redirect to previous page with correct url params
            return self._redirect_after_review(request)

        # Bulk session : we want to do something but redirect to the next pack afterwards
        if request.method == "POST" and any(
            "_continue" in key for key in request.POST.keys()
        ):
            # Save all fields
            super().changeform_view(
                request, object_id, form_url, extra_context=extra_context
            )
            # Perform the wanted action on the current pack
            pack = self.get_object(request, unquote(object_id))
            if "_approve_continue" in request.POST:
                pack.approve()
            elif "_refuse_continue" in request.POST:
                pack.refuse()
            elif "_save_continue" in request.POST:
                pack.save()

            # Redirect to the next pack
            next_ids = request.POST.get("_bulkreview_next")
            if not next_ids:
                return self._redirect_after_review(request)

            remaining_ids = next_ids.split(",")
            object_id = remaining_ids[0]
            # Create the GET parameters
            params_dict = {
                "_changelist_filters": request.GET.get("_changelist_filters"),
                "_bulkreview_next": ",".join(remaining_ids[1:]),
            }
            # add next ids in parameters without the current object id
            params = urlencode(params_dict)

            return redirect(
                reverse("admin:core_pack_change", kwargs={"object_id": str(object_id)})
                + f"?{params}"
            )

        if request.method == "GET" and "_bulkreview_next" in request.GET:
            # In case of a bulk action, get the next pack ids and add it to context
            ids = request.GET.get("_bulkreview_next")
            extra_context = {"bulk_pack_ids": ids}

        return admin.ModelAdmin.changeform_view(
            self,
            request,
            object_id=object_id,
            form_url=form_url,
            extra_context=extra_context,
        )
