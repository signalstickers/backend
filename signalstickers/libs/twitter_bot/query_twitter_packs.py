import re

from django.conf import settings
import tweepy

# Set Twitter API
auth = tweepy.OAuthHandler(
    settings.TWITTER_CONF["consumer_key"], settings.TWITTER_CONF["consumer_secret"]
)
auth.set_access_token(
    settings.TWITTER_CONF["access_token"], settings.TWITTER_CONF["access_token_secret"]
)
twitter_api = tweepy.API(auth)


def query_twitter():
    tweets = twitter_api.search(
        "signal.art -from:signalstickers", result_type="recent", count=20
    )
    signalart_urls = set()
    for tweet in tweets:
        for url in tweet.entities.get("urls", []):
            expanded_url = url.get("expanded_url", "")

            url_re = re.match(
                r"https://signal.art/addstickers/#pack_id=([\dA-Za-z]{32})&pack_key=([\dA-Za-z]{64})",
                expanded_url,
            )
            try:
                pack_id, pack_key = url_re.groups()
                source_url = "https://twitter.com/{user}/status/{tw_id}".format(
                    user=tweet.author.screen_name, tw_id=tweet.id
                )
                signalart_urls.add((pack_id, pack_key, source_url))
            except AttributeError:
                continue

    return signalart_urls
