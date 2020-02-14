import mimetypes
import re

from cloudbot import hook
from cloudbot.hook import Priority, Action
from cloudbot.util import http, web


url_re = re.compile(r'(?P<url>https?://(?:[^.]+\.)+?(?P<domain>[^: \/]+\.[^: \/]+)(?::\d+)?\/?\S*)', re.I)

skipurls = ["youtube.com", "youtu.be", "twitter.com", "steampowered.com", "reddit.com",
            "noxd.co", "worf.co", "illegalshit.com",
            "is.gd", "bit.ly", "tinyurl.com", "j.mp", "goo.gl", "youtu.be",
            "redd.it", "imgur.com", "hastebin.com", "hasteb.in"]


def get_info(url):
    if not url.startswith('//') and '://' not in url:
        url = 'http://' + url

    try:
        mimetype, encoding = mimetypes.guess_type(url)
        if mimetype and any(mimetype.startswith(t) for t in ['video', 'audio', 'image']):
            return web.try_shorten(url), None

        title = http.get_title(url)
        title = u' '.join(re.sub(u'\r|\n', u' ', title).split()).strip('| ')

        return web.try_shorten(url), title or None
    except Exception as e:
        print(e)
        return web.try_shorten(url), None


@hook.regex(url_re, priority=Priority.LOW, action=Action.HALTTYPE)
def print_url_title(match, message, logger):
    url, title = get_info(match['url'])

    if match['domain'] not in skipurls:
        message(url + (" - {title}" if title else ""))
    else:
        logger.debug(f"Link skipped: {match['domain']}")
