from django.contrib.admin.models import ADDITION as logentry_add
from django.contrib.admin.models import CHANGE as logentry_change
from django.contrib.admin.models import DELETION as logentry_deletion
from django.contrib.admin.models import LogEntry
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.models import Q

from .pack import Pack
from .tag import Tag

LOG_ADDITION = logentry_add
LOG_CHANGE = logentry_change
LOG_DELETION = logentry_deletion
LOG_CLEAR_CACHES = 13371
LOG_TWEET = 13372

LOGENTRY_TEXT = {
    LOG_ADDITION: "Added",
    LOG_CHANGE: "Changed",
    LOG_DELETION: "Deleted",
    LOG_CLEAR_CACHES: "Cleared caches",
    LOG_TWEET: "Tweeted",
}


class AdminAction(models.Model):
    """
    Used to handle logs for admin actions.
    """

    class Meta:
        managed = False

    @staticmethod
    def caches_dirty():
        try:
            last_cleared_date = (
                LogEntry.objects.filter(
                    action_flag=LOG_CLEAR_CACHES,
                    change_message__icontains='"success": true',
                )
                .order_by("action_time")
                .last()
                .action_time
            )

            last_modification = (
                LogEntry.objects.filter(
                    Q(content_type=ContentType.objects.get_for_model(Pack).pk)
                    | Q(content_type=ContentType.objects.get_for_model(Tag).pk)
                )
                .order_by("action_time")
                .last()
                .action_time
            )

            return last_modification > last_cleared_date
        except AttributeError:
            return None
