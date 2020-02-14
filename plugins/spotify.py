import re

from cloudbot import hook
from cloudbot.bot import bot
from cloudbot.util import http, web


gateway = "http://play.spotify.com/{}/{}"  # http spotify gw address


def sptfy(text, sptfy=False):
    if sptfy:
        shortenurl = "http://sptfy.com/index.php"
        data = {"longUrl": text, "shortUrlDomain": 1, "submitted": 1, "shortUrlFolder": 6, "customUrl": "",
                "shortUrlPassword": "", "shortUrlExpiryDate": "", "shortUrlUses": 0, "shortUrlType": 0}
        try:
            soup = http.get_soup(shortenurl, data=data, cookies=True)
        except:
            return text
        try:
            link = soup.find("div", {"class": "resultLink"}).text.strip()
            return link
        except:
            message = "Unable to shorten URL: %s" % \
                      soup.find("div", {"class": "messagebox_text"}).find("p").text.split("<br/>")[0]
            return message
    else:
        return web.try_shorten(text)


@hook.command
def spotify(text):
    """[-track|-artist|-album] <search term> - Search for specified media via Spotify; defaults to track."""
    api_key = bot.config.get_api_key("spotify")
    if not api_key:
            return "This command requires a Spotify API key."

    text = text.split(" ")
    if len(text) > 1 and text[0] in ["-track", "-artist", "-album"]:
        kind, query = text.pop(0)[1:], " ".join(text)
    else:
        kind, query = "track", " ".join(text)

    try:
        params = {"grant_type": "client_credentials"}
        access_token = http.get_json("https://accounts.spotify.com/api/token",
            auth=True, auth_keys=api_key, get_method="POST", data=params)["access_token"]
    except Exception as e:
        return f"Could not get access token: {e}"


    try:
        data = http.get_json("https://api.spotify.com/v1/search/", type=kind, q=query, limit=1,
                             headers={"Authorization": "Bearer " + access_token})
    except Exception as e:
        return f"Could not get {kind} information: {e}"

    try:
        type, id = data[kind+"s"]["items"][0]["uri"].split(":")[1:]
    except IndexError as e:
        return f"Could not find {kind}."
    url = sptfy(gateway.format(type, id))

    if kind == "track":
        return "\x02{}\x02 by \x02{}\x02 - {}".format(data[kind+"s"]["items"][0]["name"], data[kind+"s"]["items"][0]["artists"][0]["name"], url)
    else:
        return "\x02{}\x02 - {}".format(data[kind+"s"]["items"][0]["name"], url)

