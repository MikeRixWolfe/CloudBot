import re

from cloudbot import hook
from cloudbot.bot import bot
from cloudbot.util import http, web


base_url = 'https://www.googleapis.com/youtube/v3/'
search_url = base_url + 'search'
video_url = base_url + 'videos'
short_url = "http://youtu.be/"

youtube_re = re.compile(r'(?:youtube.*?(?:v=|/v/)|youtu\.be/|yooouuutuuube.*?id=)([-_a-z0-9]+)', re.I)
output_format = u'{url} - \x02{title}\x02 - \x02{channelTitle}\x02 [{time}] [{views:,} views]'


def get_youtube_info(video_id, api_key=None):
    params = {
        "id": video_id,
        "key": api_key,
        "part": "snippet,contentDetails,statistics"
    }
    result = http.get_json(video_url, params=params)

    if result.get('error') or not result.get('items') or len(result['items']) < 1:
        return web.try_shorten(short_url+video_id)

    playtime = result['items'][0]['contentDetails']['duration'].strip('PT').lower()
    views = int(result['items'][0]['statistics']['viewCount'])
    return output_format.format(url=web.try_shorten(short_url+video_id), time=playtime,
                                views=views, **result['items'][0]['snippet'])


@hook.regex(youtube_re)
def youtube_url(match, message):
    api_key = bot.config.get_api_key("google").get("access")
    message(get_youtube_info(match.group(1), api_key))


@hook.command('youtube', 'yt', 'y')
def youtube(text, message):
    """<query> - Returns the first YouTube search result for <query>."""
    api_key = bot.config.get_api_key("google").get("access")
    if not api_key:
        return "This command requires a Google Developers Console API key."

    params = {
        "q": text,
        "key": api_key,
        "part": "snippet",
        "safeSearch": "none",
        "maxResults": 1,
        "type": "video"
    }
    try:
        result = http.get_json(search_url, params=params)
    except Exception as e:
        return "Error accessing Youtube, please try again in a few minutes."

    if result.get('error') or not result.get('items') or len(result['items']) < 1:
        return "None found."

    message(get_youtube_info(result['items'][0]['id']['videoId'], api_key))
