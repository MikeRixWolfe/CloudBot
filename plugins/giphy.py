from random import choice

from cloudbot import hook
from cloudbot.bot import bot
from cloudbot.util import http


@hook.command
def gif(text, message):
    """<query> - Returns first giphy search result."""
    api_key = bot.config.get_api_key("giphy")
    if not api_key:
        return "This command requires an API key from giphy.com."

    url = 'http://api.giphy.com/v1/gifs/search'
    try:
        response = http.get_json(url, q=text, limit=5, api_key=api_key)
    except http.HTTPError as e:
        return e.msg

    try:
        message(choice(response['data'])['bitly_gif_url'])
    except:
        message('No results found.')

