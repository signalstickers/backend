from .models import Pack


def admin_navbar(request):
    if request.user.is_staff:
        return {"packs_to_review": Pack.objects.filter(status="IN_REVIEW").count()}
    return {}
