from api.utils import remove_empty_values
from core.models import Pack, Tag
from rest_framework import serializers


class TagSlugRelatedField(serializers.SlugRelatedField):
    def to_internal_value(self, data):
        return data


class PackSerializer(serializers.ModelSerializer):
    tags = TagSlugRelatedField(
        many=True, slug_field="name", queryset=Tag.objects.none()
    )

    class Meta:
        model = Pack
        fields = (
            "pack_id",
            "pack_key",
            "source",
            "tags",
            "nsfw",
            "original",
            "editorschoice",
        )

    def to_representation(self, instance):
        pack_tags_names = [tag.name for tag in instance.tags.all()]
        # Furry packs should only contain a "furry" tag
        if "furry" in pack_tags_names:
            pack_tags_names = ["furry"]

        return remove_empty_values(
            {
                "meta": {
                    "id": instance.pack_id,
                    "key": instance.pack_key,
                    "source": instance.source,
                    "tags": pack_tags_names,
                    "nsfw": instance.nsfw,
                    "original": instance.original,
                    "animated": instance.animated,
                    "editorschoice": instance.editorschoice,
                    "totalviews": instance.total_views,
                    "hotviews": instance.hot_views,
                },
                "manifest": {
                    "title": instance.title,
                    "author": instance.author,
                    "cover": {"id": instance.id_cover},
                },
            }
        )
