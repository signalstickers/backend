from core.models import AdminAction, Pack


def admin_navbar(request):
    if request.user.is_staff:
        return {
            "packs_to_review": Pack.objects.in_review_count(),
            "packs_escalated": Pack.objects.escalated_count(),
            "caches_dirty": AdminAction.caches_dirty(),
        }
    return {}
