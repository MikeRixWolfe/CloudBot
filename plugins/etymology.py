import re

from cloudbot import hook
from cloudbot.util import formatting, http


@hook.command("etymology", "ety")
def etymology(text, message):
    """<word> - Retrieves the etymology of chosen word."""
    url = 'http://www.etymonline.com/search'
    try:
        params = {'q': text}
        h = http.get_html(url, params=params)
    except:
        return "Error fetching etymology."
    etym = h.xpath('//section')

    if not etym:
        return 'No etymology found for ' + text

    etym = etym[0].text_content()
    etym = ' '.join(etym.split())

    message(formatting.truncate_str(etym, 400))

