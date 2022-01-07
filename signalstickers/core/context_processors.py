from core.models import Pack


def admin_navbar(request):
    if request.user.is_staff:
        return {"packs_to_review": Pack.objects.in_review_count()}
    return {}
