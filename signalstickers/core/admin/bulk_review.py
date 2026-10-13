from urllib.parse import urlencode

from django.shortcuts import redirect
from django.urls import reverse

LAST_PACK = "__last"


def parse_next_ids(raw):
    """Split a ``_bulkreview_next`` value into the list of remaining pack ids."""
    if not raw or raw == LAST_PACK:
        return []
    return raw.split(",")


def redirect_to_next_pack(object_id, remaining_ids, changelist_filters):
    """Build the redirect to the next pack of a bulk review session."""
    params = urlencode(
        {
            "_changelist_filters": changelist_filters,
            "_bulkreview_next": ",".join(remaining_ids) or LAST_PACK,
        }
    )
    return redirect(
        reverse("admin:core_pack_change", kwargs={"object_id": str(object_id)})
        + f"?{params}"
    )
