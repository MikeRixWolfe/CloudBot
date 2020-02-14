from cloudbot import hook
from cloudbot.bot import bot
from cloudbot.util import http, web

api_url = "https://translate.yandex.net/api/v1.5/tr.json/"
lang_dict = {}
lang_dir = []


@hook.on_start()
def load_key():
    api_key = bot.config.get_api_key("yandex_translate")
    if not api_key:
        return

    url = api_url + "getLangs"
    params = {
        'key': api_key,
        'ui': 'en'
    }
    data = http.get_json(url, params=params)
    lang_dict.clear()
    lang_dir.clear()
    lang_dict.update(dict((v, k) for k, v in data['langs'].items()))
    lang_dir.extend(data['dirs'])


def check_code(code):
    """checks the return code for the calls to yandex"""
    codes = {
        401: 'Invalid API key.',
        402: 'This API key has been blocked',
        403: 'The daily limit for requests has been reached',
        404: 'The daily limit of translated text has been reached',
        413: 'The text exceeds the maximum',
        422: 'The text could not be translated',
        501: 'The specified translation direction is not supported'
    }
    try:
        out = codes[code]
    except LookupError:
        out = "The API returned an undocumented error."
    return out


@hook.command("langlist", "tlist", autohelp=False)
def list_langs():
    """- List the languages/codes that can be used to translate. Translation is powered by Yandex
    https://translate.yandex.com"""
    api_key = bot.config.get_api_key("yandex_translate")
    if not api_key:
        return "This command requires a Yandex Translate API key"

    url = api_url + "getLangs"
    params = {
        'key': api_key,
        'ui': 'en'
    }
    data = http.get_json(url, params=params)
    langs = data['langs']
    out = "Language Codes:"
    out += ",".join("\n{}-{}".format(key, value) for (key, value) in sorted(langs.items()))
    out += "\n\nTranslation directions:"
    out += ",".join("\n{}".format(code) for code in data['dirs'])
    paste = web.paste(out, ext="txt")
    return "Here is information on what I can translate as well as valid language codes. {}".format(paste)


@hook.command("tran", "translate")
def trans(text, reply, event):
    """
    <language or language code> <text to translate> - Translation is
    Powered by Yandex https://translate.yandex.com
    """
    api_key = bot.config.get_api_key("yandex_translate")
    if not api_key:
        return "This command requires a Yandex Translate API key"

    inp = text.split(' ', 1)
    if len(inp) < 2:
        event.notice_doc()
        return None

    lang = inp[0].replace(':', '')
    text = inp[1]
    if lang.title() in lang_dict.keys():
        lang = lang_dict[lang.title()]
    elif lang not in lang_dict.values() and lang not in lang_dir:
        return "Please specify a valid language, language code, to translate to. Use .langlist for more information " \
               "on language codes and valid translation directions."
    url = api_url + "translate"
    params = {
        'key': api_key,
        'lang': lang,
        'text': text,
        'options': 1
    }

    try:
        data = http.get_json(url, params=params)
    except Exception:
        reply("Unknown error occurred.")
        raise

    out = "Translation ({}): {}".format(data['lang'], data['text'][0])
    return out
