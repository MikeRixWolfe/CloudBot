import random
import re

from cloudbot import hook
from cloudbot.bot import bot
from cloudbot.util import formatting, http, web


base_url = 'https://www.googleapis.com/customsearch/v1'


def custom_get(query, key, is_image=None, num=1):
    params = {
        "q": query,
        "cx": key['cx'],
        "key": key['access'],
        "num": num,
        "fields": "items(title,link,snippet)",
        "safe": "off"
    }

    if is_image:
        params["searchType"] = "image"

    return http.get_json(base_url, params=params)


@hook.command('gis')
def googleimage(text, message):
    """<query> - Returns a random image from the first 10 Google Image results for <query>."""
    api_key = dev_key = bot.config.get_api_key("google")
    if not api_key:
        return "This command requires a Google Developers Console API key."

    try:
        parsed = custom_get(text, api_key, is_image=True, num=1)
    except Exception as e:
        return "Error: {}".format(e)
    if 'items' not in parsed:
        return "No results"

    message(web.try_shorten(random.choice(parsed['items'])['link']))


@hook.command('google', 'g')
def google(text, message):
    """<query> - Returns first Google search result for <query>."""
    api_key = dev_key = bot.config.get_api_key("google")
    if not api_key:
        return "This command requires a Google Developers Console API key."

    try:
        parsed = custom_get(text, api_key)
    except Exception as e:
        return "Error: {}".format(e)
    if 'items' not in parsed:
        return "No results"

    link = web.try_shorten(parsed['items'][0]['link'])
    title = formatting.truncate_str(parsed['items'][0]['title'], 250)
    title = ' '.join(re.sub('\r|\n', ' ', title).split()).strip('| ')
    message(f"{link} - \x02{title}\x02")


@hook.command
def map(text, message):
    """<place>|<origin to destination> - Gets a Map of place or route from Google Maps."""
    message(web.try_shorten("https://www.google.com/maps/?q={}".format(http.quote_plus(text))))
