import re

from cloudbot import hook
from cloudbot.util import http, web, formatting

steam_re = re.compile(r'.*://store.steampowered.com/app/([0-9]+)?.*', re.I)

API_URL = "http://store.steampowered.com/api/appdetails/"
STORE_URL = "http://store.steampowered.com/app/{}/"


def format_game(app_id, show_url=True):
    """
    Takes a Steam Store app ID and returns a formatted string with data about that app ID
    :type app_id: string
    :return: string
    """
    params = {'appids': app_id}

    try:
        data = http.get_json(API_URL, params=params, timeout=15)
    except Exception as e:
        return f"Could not get game info: {e}"

    game = data[app_id]["data"]

    # basic info
    out = ["\x02{}\x02".format(game["name"])]

    desc = " ".join(formatting.strip_html(game["about_the_game"]).split())
    out.append(formatting.truncate(desc, 75))

    # genres
    try:
        genres = ", ".join([g['description'] for g in game["genres"]])
        out.append("\x02{}\x02".format(genres))
    except KeyError:
        # some things have no genre
        pass

    # release date
    if game['release_date']['coming_soon']:
        out.append("coming \x02{}\x02".format(game['release_date']['date']))
    else:
        out.append("released \x02{}\x02".format(game['release_date']['date']))

    # pricing
    if game['is_free']:
        out.append("\x02free\x02")
    elif not game.get("price_overview"):
        # game has no pricing, it's probably not released yet
        pass
    else:
        price = game['price_overview']

        # the steam API sends prices as an int like "9999" for $19.99, we divmod to get the actual price
        if price['final'] == price['initial']:
            out.append("\x02$%d.%02d\x02" % divmod(price['final'], 100))
        else:
            price_now = "$%d.%02d" % divmod(price['final'], 100)
            price_original = "$%d.%02d" % divmod(price['initial'], 100)

            out.append("\x02{}\x02 (was \x02{}\x02)".format(price_now, price_original))

    if show_url:
        url = web.try_shorten(STORE_URL.format(game['steam_appid']))
        out.append(url)

    return " - ".join(out)


@hook.command()
def steam(text, message):
    """<query> - Search for specified game/trailer/DLC"""
    params = {'term': text.strip().lower()}

    try:
        data = http.get_soup("http://store.steampowered.com/search/", params=params)
    except Exception as e:
        return "Could not get game info: {}".format(e)

    result = data.find('a', {'class': 'search_result_row'})

    if not result:
        return "No game found."

    app_id = result['data-ds-appid']
    message(format_game(app_id))


@hook.regex(steam_re)
def steam_url(match, message):
    app_id = match.group(1)
    message(format_game(app_id, show_url=False))

