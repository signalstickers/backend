from core.models import AdminAction, Pack, Report


def admin_navbar(request):
    if request.user.is_staff:
        return {
            "packs_to_review": Pack.objects.in_review_count(),
            "packs_escalated": Pack.objects.escalated_count(),
            "reports_to_process": Report.objects.to_process_count(),
            "caches_dirty": AdminAction.caches_dirty(),
        }
    return {}
