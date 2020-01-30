import re
import logging
import requests

from cloudbot import hook
from cloudbot.bot import bot


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

    return max(dict(match()).iteritems(), key=lambda x: (x[1], len(x[0])))[0]


#@hook.api_key('ipapi')
@hook.command
async def geoip(text, reply, loop):
    """geoip <IP address> - Gets the location of an IP address."""
    api_key = bot.config.get_api_key("giphy")
    url = "http://api.ipapi.com/%s" % (http.quote(text.encode('utf8'), safe=''))

    try:
        data = requests.get(url, params={'access_key': api_key}).json()
    except:
        return "I couldn't find %s" % inp

    return fformat(data).replace('in United', 'in the United')

