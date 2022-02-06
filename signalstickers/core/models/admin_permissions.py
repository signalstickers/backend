from django.db import models


class AdminPermissions(models.Model):
    class Meta:

        managed = False
        default_permissions = ()
        permissions = (
            ("view_stats_page", "View stats page"),
            ("invalidate_cloudflare", "Invalidate CloudFlare caches"),
            ("trigger_tweets", "Trigger tweets"),
        )
