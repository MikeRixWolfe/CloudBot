from cloudbot import hook
from cloudbot.bot import bot
from cloudbot.util import http, web

url = 'https://www.alphavantage.co/query'


def tryParse(value):
    try:
        return float(value.strip('%'))
    except ValueError:
        return value


@hook.command()
def stock(text):
    """<symbol> - Looks up stock information"""
    api_key = bot.config.get_api_key("alphavantage")
    if not api_key:
        return "This command requires an Alpha Vantage API key."

    params = {'function': 'GLOBAL_QUOTE', 'apikey': api_key, 'symbol': text}
    quote = http.get_json(url, params=params)

    if not quote.get("Global Quote"):
        return "Unknown ticker symbol '{}'".format(text)

    quote = {k.split(' ')[-1]:tryParse(v) for k,v in quote['Global Quote'].items()}

    quote['url'] = web.try_shorten('https://finance.yahoo.com/quote/' + text)

    try:
        if float(quote['change']) < 0:
            quote['color'] = "5"
        else:
            quote['color'] = "3"

        return "{symbol} - ${price:.2f} " \
            "\x03{color}{change:+.2f} ({percent:.2f}%)\x0F " \
            "H:${high:.2f} L:${low:.2f} O:${open:.2f} " \
            "Volume:{volume} - {url}".format(**quote)
    except:
        return "Error parsing return data, please try again later."
