from stickers.models import Pack, Tag
from django.contrib import admin
from django.db.models import Count


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    # def packs_count(self, obj):
    #     return obj.pack_set.count()

    search_fields = ("name",)
    list_display = ("name", "_packs_count")

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(packs_count=Count("packs"))

    def _packs_count(self, obj):
        return obj.packs_count

    _packs_count.admin_order_field = "packs_count"
    _packs_count.short_description = "Packs using this tag"
