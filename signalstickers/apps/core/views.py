from io import StringIO

from django.contrib import messages
from django.core.management import call_command
from django.shortcuts import render
from django.utils.html import format_html
from django.views.generic import View

from apps.core.services import invalidate_cdn, tweet_command
from apps.stickers.models import Pack


class AdminTriggerActionsView(View):
    def get(self, request):
        return render(
            request,
            "admin/trigger_actions.html",
            context={"nb_not_tweeted": Pack.objects.not_twitteds().count()},
        )

    def post(self, request):
        if request.POST.get("action") == "cloudflareclear":

            success, output = invalidate_cdn()

            if success:
                messages.success(
                    request,
                    format_html(
                        "Cloudflare caches cleared. Output: <code>{}</code>", output
                    ),
                )
            else:
                messages.error(
                    request,
                    format_html(
                        "Error when invalidating caches: <code>{}</code>", output
                    ),
                )

        elif request.POST.get("action") == "tweet":

            nb_packs_tweeted, errs = tweet_command()

            if nb_packs_tweeted:
                messages.success(request, f"Packs twitted: {nb_packs_tweeted}.")
            else:
                messages.error(
                    request,
                    format_html(
                        "No pack has been tweeted. Errors: <code>{}</code>", errs
                    ),
                )

        return render(
            request,
            "admin/trigger_actions.html",
            context={"nb_not_tweeted": Pack.objects.not_twitteds().count()},
        )
