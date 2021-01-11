from django.core.cache import cache
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from stickers.models import Pack


def _clear_packs_view_caches():
    cache.delete("view__api_packs_list")


@receiver(post_save, sender=Pack)
def clear_packs_view_caches_save(*args, **kwargs):
    _clear_packs_view_caches()


@receiver(post_delete, sender=Pack)
def clear_packs_view_caches_delete(*args, **kwargs):
    _clear_packs_view_caches()
