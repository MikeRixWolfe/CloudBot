from json import dumps

from cloudbot.bot import bot
from cloudbot.util import http


short_url = "https://noxd.co"
paste_url = "https://hastebin.com"
#paste_url = "http://hasteb.in"


def shorten(url):
    """ shortens a URL with the goo.gl API """
    api_key = bot.config.get_api_key('noxd')
    postdata = {'api_key': api_key, 'link': url}

    request = http.get_json(short_url, data=postdata, get_method='POST')
    return "{}/{}".format(short_url, request['Id'])


def try_shorten(url):
    try:
        out = shorten(url)
    except:
        out = url
    return out


def paste(text, ext='txt'):
    """ pastes text to a hastebin server """
    data = http.get_json(paste_url + "/documents", data=text, get_method='POST')
    return "{}/{}.{}".format(paste_url, data['key'], ext)

