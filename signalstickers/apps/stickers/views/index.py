from urllib.parse import parse_qs, urlparse

from apps.stickers.models import Pack, PackStatus
from django.shortcuts import render
from django.views import View


class IndexView(View):
    def get(self, request):
        return render(request, "check_pack.html", {})

    def post(self, request):

        pack_url = request.POST.get("packurl")
        pack_info = parse_qs(urlparse(pack_url).fragment)

        try:
            pack = Pack.objects.get(
                pack_id=pack_info["pack_id"][0], pack_key=pack_info["pack_key"][0]
            )
            return render(
                request,
                "check_pack.html",
                {
                    "error": "",
                    "status": PackStatus[pack.status].name,
                    "status_comments": pack.status_comments,
                    "url": pack_url,
                    "pack_id": pack.pack_id,
                },
            )
        except:
            return render(
                request, "check_pack.html", {"error": "No pack found.", "url": pack_url}
            )

