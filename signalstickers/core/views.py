from statistics import mean, median

from core.models import LOG_CLEAR_CACHES, LOG_TWEET, AdminAction, Pack, SiteStat
from core.services import invalidate_cdn, tweet_command
from core.utils import get_current_ym_date, get_last_month_ym_date
from django.contrib import messages
from django.contrib.admin.models import LogEntry
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import PermissionDenied
from django.shortcuts import render
from django.utils.html import format_html
from django.views.generic import View


class AdminTriggerActionsView(View):
    def get(self, request, admin_site):
        context = dict(
            admin_site.each_context(request),
            nb_not_tweeted=Pack.objects.not_twitteds().count(),
        )
        return render(request, "admin/trigger_actions.html", context=context)

    def post(self, request, admin_site):
        def clear_caches():
            if not request.user.has_perm("core.invalidate_cloudflare"):
                raise PermissionDenied()

            success, output = invalidate_cdn()
            if success:
                messages.success(
                    request,
                    format_html(
                        "Cloudflare caches cleared. Output: <code>{}</code>", output
                    ),
                )
                LogEntry.objects.log_action(
                    user_id=request.user.id,
                    content_type_id=ContentType.objects.get_for_model(AdminAction).pk,
                    object_id="",
                    object_repr="",
                    action_flag=LOG_CLEAR_CACHES,
                    change_message=f"Cloudflare caches cleared. Output: {output}",
                )
            else:
                messages.error(
                    request,
                    format_html(
                        "Error when invalidating caches: <code>{}</code>", output
                    ),
                )
                LogEntry.objects.log_action(
                    user_id=request.user.id,
                    content_type_id=ContentType.objects.get_for_model(AdminAction).pk,
                    object_id="",
                    object_repr="",
                    action_flag=LOG_CLEAR_CACHES,
                    change_message=f"Error when invalidating caches: {output}",
                )

        def tweet():
            if not request.user.has_perm("core.trigger_tweets"):
                raise PermissionDenied()

            nb_packs_tweeted, errs = tweet_command()
            if nb_packs_tweeted:
                success_message = f"Packs twitted: {nb_packs_tweeted}."
                messages.success(request, success_message)

                LogEntry.objects.log_action(
                    user_id=request.user.id,
                    content_type_id=ContentType.objects.get_for_model(AdminAction).pk,
                    object_id="",
                    object_repr="",
                    action_flag=LOG_TWEET,
                    change_message=success_message,
                )

            else:
                messages.error(
                    request,
                    format_html(
                        "No pack has been tweeted. Errors: <code>{}</code>", errs
                    ),
                )
                LogEntry.objects.log_action(
                    user_id=request.user.id,
                    content_type_id=ContentType.objects.get_for_model(AdminAction).pk,
                    object_id="",
                    object_repr="",
                    action_flag=LOG_TWEET,
                    change_message=f"No pack tweeted: {errs}",
                )

        if request.POST.get("action") == "cloudflareclear_and_tweet":
            clear_caches()
            tweet()
        elif request.POST.get("action") == "cloudflareclear":
            clear_caches()
        elif request.POST.get("action") == "tweet":
            tweet()

        context = dict(
            admin_site.each_context(request),
            nb_not_tweeted=Pack.objects.not_twitteds().count(),
        )

        return render(request, "admin/trigger_actions.html", context=context)


class AdminStatsView(PermissionRequiredMixin, View):
    permission_required = "core.view_stats_page"

    def get(self, request, admin_site):

        # Compute basic stats
        visits_by_month = SiteStat.objects.get_visits_by_month()
        visits_by_month_values = visits_by_month.values()
        homepage_this_month = list(visits_by_month.values())[-1]
        all_times_mean = int(mean(visits_by_month_values))
        all_times_med = int(median(visits_by_month_values))
        all_times_max = max(visits_by_month_values)

        context = dict(
            admin_site.each_context(request),
            most_popular_this_month=Pack.objects.most_popular_for_month(
                month=get_current_ym_date(), nbr=50
            ),
            most_popular_last_month=Pack.objects.most_popular_for_month(
                month=get_last_month_ym_date(), nbr=50
            ),
            packs_views_by_month=Pack.objects.total_packviews(),
            visits_by_month=visits_by_month,
            most_viewed_packs_all_times=Pack.objects.most_viewed_packs(nbr=50),
            all_times_mean=all_times_mean,
            all_times_med=all_times_med,
            all_times_max=all_times_max,
            homepage_this_month=homepage_this_month,
        )

        return render(request, "admin/stats.html", context=context)
