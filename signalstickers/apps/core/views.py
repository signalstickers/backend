from io import StringIO

from django.contrib import messages
from django.core.management import call_command
from django.shortcuts import render
from django.utils.safestring import mark_safe
from django.views.generic import View

from apps.core.services import publish_command, tweet_command
from apps.stickers.models import Pack


class AdminTriggerActionsView(View):
    def get(self, request):
        return render(
            request,
            "admin/trigger_actions.html",
            context={"nb_not_tweeted": Pack.objects.not_twitteds().count()},
        )

    def post(self, request):
        if request.POST.get("action") == "publish":

            success, message = publish_command()

            if success:
                messages.success(
                    request,
                    mark_safe(f"Publication triggered. Output: <code>{message}</code>"),
                )
            else:
                messages.error(
                    request,
                    mark_safe(f"Publication aborted. Output: <code>{message}</code>"),
                )

        elif request.POST.get("action") == "tweet":

            nb_packs_tweeted, errs = tweet_command()

            if nb_packs_tweeted:
                messages.success(request, f"Packs twitted: {nb_packs_tweeted}.")
            else:
                messages.error(request, f"No pack has been tweeted. Errors: {errs}")

        return render(
            request,
            "admin/trigger_actions.html",
            context={"nb_not_tweeted": Pack.objects.not_twitteds().count()},
        )
