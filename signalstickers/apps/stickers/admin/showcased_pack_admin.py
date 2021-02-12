from adminsortable2.admin import SortableAdminMixin
from apps.stickers.models import ShowcasedPack
from django.contrib import admin


@admin.register(ShowcasedPack)
class ShowcasedPackAdmin(SortableAdminMixin, admin.ModelAdmin):
    autocomplete_fields = ("pack",)
