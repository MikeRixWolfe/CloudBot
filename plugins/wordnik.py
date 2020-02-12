import re
import random

from cloudbot import hook
from cloudbot.util import http, formatting

API_URL = 'http://api.wordnik.com/v4/'
WEB_URL = 'https://www.wordnik.com/words/{}'


@hook.command
def define(text, message):
    """<word> - Returns a definition for <word> from wordnik.com."""
    # based on edwardslabs/cloudbot's wordnik.py
    api_key = bot.config.get_api_key("wordnik")
    if not api_key:
        return "This command requires an API key from wordnik.com."

    word = text.split(' ')[0]
    url = API_URL + u"word.json/{}/definitions".format(word)

    try:
        params = {'api_key': api_key, 'limit': 1, 'useCanonical': 'false'}
        json = http.get_json(url, params=params)
    except:
        return "Wordnik API error; please try again in a few minutes."

    if json:
        data = json[0]

        message(u"\x02{word}\x02: {text}".format(**data))
    else:
        return "I could not find a definition for \x02{}\x02.".format(word)


@hook.command("wotd", autohelp=False)
def wordoftheday(text, message):
    """- Returns the word of the day from wordnik.com."""
    api_key = bot.config.get_api_key("wordnik")
    if not api_key:
        return "This command requires an API key from wordnik.com."

    url = API_URL + "words.json/wordOfTheDay"

    try:
        params = {'api_key': api_key}
        json = http.get_json(url, params=params)
    except:
        return "Wordnik API error; please try again in a few minutes."

    if json:
        word = json['word']
        note = json['note']
        pos = json['definitions'][0]['partOfSpeech']
        definition = json['definitions'][0]['text']
        message(u"The word the day is \x02{}\x0F: ({}) {} {}".format(word, pos, definition, note))
    else:
        return "Sorry I couldn't find the word of the day."

