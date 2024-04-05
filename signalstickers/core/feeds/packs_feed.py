from core.models.pack import Pack
from core.utils import is_url
from django.contrib.syndication.views import Feed
from django.utils.feedgenerator import Atom1Feed


class RssPackFeed(Feed):
    title = "Signalstickers"
    link = "https://signalstickers.org/"
    description = "Updates on new packs on signalstickers.org! Atom feed is also available at /feed/atom/"

    description_template = "feeds/item_description.html"

    def items(self):
        return Pack.objects.onlines()[:10]

    def item_link(self, item):
        return f"https://signalstickers.org/pack/{item.pack_id}"

    def item_author_name(self, item):
        return item.author

    def item_author_link(self, item):
        if is_url(item.author):
            return item.author
        return None

    def item_categories(self, item):
        return [tag.name for tag in item.tags.all()]

    # FIXME remove if item_categories() works OK
    # def get_context_data(self, **kwargs):
    #     context = super().get_context_data(**kwargs)

    #     pack_tags = kwargs["item"].tags.all()
    #     pack_tags_list = [tag.name for tag in pack_tags[:10]]
    #     if len(pack_tags) > 10:
    #         pack_tags_list.append(f"... (+ {len(pack_tags) - 10})")

    #     context["tags"] = pack_tags_list
    #     return context


class AtomPackFeed(RssPackFeed):
    feed_type = Atom1Feed
    subtitle = "Updates on new packs on signalstickers.org! RSS feed is also available at /feed/rss/"
