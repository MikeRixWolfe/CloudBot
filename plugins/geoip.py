import re
import logging
import requests

from cloudbot import hook
from cloudbot.bot import bot
from cloudbot.util import http

formats = [
    "{ip} seems to be located in {city}, {region_name} in {country_name}",
    "{ip} seems to be located in {city} in {country_name}",
    "{ip} seems to be located in {region_name} in {country_name}",
    "{ip} seems to be located in {country_name}",
    "Unable to locate geolocation information for the given location"
]


def fformat(args):
    """find format string for args based on number of matches"""
    def match():
        for f in formats:
            try:
                yield f.format(**args), len(re.findall(r'(\{.*?\})',f))
            except:
                pass

    return max(dict(match()).items(), key=lambda x: (x[1], len(x[0])))[0]


@hook.command
async def geoip(text, reply, loop):
    """<IP address> - Gets the location of an IP address."""
    api_key = bot.config.get_api_key("ipapi")
    if not api_key:
        return "This command requires an API key from ipapi.com."

    url = "http://api.ipapi.com/" + http.quote(text.encode('utf8'), safe='')

    try:
        data = http.get_json(url, access_key=api_key)
    except:
        return f"I couldn't find {text}"

    return fformat(data).replace('in United', 'in the United')

