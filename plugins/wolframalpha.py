import re
import urllib.parse

from cloudbot import hook
from cloudbot.util import http, web, formatting

api_url = 'http://api.wolframalpha.com/v2/query'
query_url = 'http://www.wolframalpha.com/input/?i={}'


@hook.command("wa")
def wolframalpha(text, bot):
    """<query> - Computes <query> using Wolfram Alpha."""
    api_key = bot.config.get_api_key("wolframalpha")
    if not api_key:
        return  "This command requires a Wolfram Alpha API key."

    try:
        params = {'input': text, 'appid': api_key}
        data = http.get_xml(api_url, params=params)
    except:
        return "WolframAlpha API error, please try again in a few minutes."

    pod_texts = []
    for pod in data.xpath("//pod[@primary='true']"):
        title = pod.attrib['title']
        if pod.attrib['id'] == 'Input':
            continue

        results = []
        for subpod in pod.xpath('subpod/plaintext/text()'):
            subpod = subpod.strip().replace('\\n', '; ')
            subpod = re.sub(r'\s+', ' ', subpod)
            if subpod:
                results.append(subpod)
        if results:
            pod_texts.append(title + ': ' + ', '.join(results))

    ret = ' - '.join(pod_texts)

    if not pod_texts:
        return 'No results.'

    # I have no idea what this regex does.
    ret = re.sub(r'\\(.)', r'\1', ret)
    ret = formatting.truncate(ret, 250)

    if not ret:
        return 'No results.'

    return ret

