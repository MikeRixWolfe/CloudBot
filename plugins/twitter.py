import random
import re
import time
from time import strptime, strftime
from urllib.parse import quote

from cloudbot import hook
from cloudbot.bot import bot
from cloudbot.util import http, web


twitter_re = re.compile(r'https?://(?:mobile.)?twitter.com/(.+?)/status/(\d+)', re.I)

@hook.command
def twitter(text, message):
    """<user|user n|id|#search|#search n> - Get <user>'s last/<n>th tweet/get tweet <id>/do <search>/get <n>th <search> result."""
    api_key = bot.config.get_api_key("twitter")
    if not api_key:
        return "This command requires a Twitter API key."

    if not isinstance(api_key, dict) or any(key not in api_key for key in
                                            ('consumer', 'consumer_secret', 'access', 'access_secret')):
        return "error: api keys not set"

    getting_id = False
    doing_search = False
    index_specified = False

    if re.match(r'^\d+$', text):
        getting_id = True
        request_url = "https://api.twitter.com/1.1/statuses/show.json?id=%s" % text
    else:
        try:
            text, index = re.split('\s+', text, 1)
            index = int(index.strip('-'))
            index_specified = True
        except ValueError:
            index = 0
        if index < 0:
            index = 0
        if index >= 20:
            return 'Error: only supports up to the 20th tweet'

        if re.match(r'^#', text):
            doing_search = True
            request_url = "https://api.twitter.com/1.1/search/tweets.json"
            params = {'q': quote(text)}
        else:
            request_url = "https://api.twitter.com/1.1/statuses/user_timeline.json"
            params = {'screen_name': text, 'exclude_replies': True, 'include_rts': False, 'tweet_mode': 'extended'}

    try:
        tweet = http.get_json(request_url, params=params, oauth=True, oauth_keys=api_key)
    except http.HTTPError as e:
        errors = {400: 'bad request (ratelimited?)',
                  401: 'unauthorized (private)',
                  403: 'forbidden',
                  404: 'invalid user/id',
                  500: 'twitter is broken',
                  502: 'twitter is down ("getting upgraded")',
                  503: 'twitter is overloaded (lol, RoR)',
                  410: 'twitter shut off api v1.'}
        if e.code == 404:
            return 'Error: invalid ' + ['username', 'tweet id'][getting_id]
        if e.code in errors:
            return 'Error: ' + errors[e.code]
        return 'Error: unknown %s' % e.code

    if doing_search:
        try:
            tweet = tweet["statuses"]
            if not index_specified:
                index = random.randint(0, len(tweet) - 1)
        except:
            return 'Error: no results'

    if not getting_id:
        try:
            tweet = tweet[index]
        except IndexError:
            return 'Error: not that many tweets found'

    tweet['full_text'] = http.h.unescape(tweet['full_text'])
    if tweet['full_text'].count('\n') > 0:
        tweet['full_text'] = re.sub(r'(.*?)(https:\/\/t.co\/.*)', r'\1\n\2', tweet['full_text'])
        message(u'{} (@{}) on Twitter:'.format(tweet['user']['name'], tweet['user']['screen_name']))
        for line in tweet['full_text'].split('\n'):
            if len(line.strip()) > 0:
                message(u'   {}'.format(line))
    else:
        message(u'{} (@{}) on Twitter: "{}"'.format(tweet['user']['name'],
            tweet['user']['screen_name'], tweet['full_text'].replace('\n', ' | ')))


@hook.regex(twitter_re)
def twitter_url(match, message):
    try:
        api_key = bot.config.get_api_key("twitter")
        request_url = 'https://api.twitter.com/1.1/statuses/show.json'
        params = {'id': match.group(2), 'tweet_mode': 'extended'}
        tweet = http.get_json(request_url, params=params, oauth=True, oauth_keys=api_key)

        tweet['full_text'] = http.h.unescape(tweet['full_text'])
        if tweet['full_text'].count('\n') > 0:
            tweet['full_text'] = re.sub(r'(.*?)(https:\/\/t.co\/.*)', r'\1\n\2', tweet['full_text'])
            message(u'{} - {} (@{}) on Twitter:'.format(web.try_shorten(match.group(0)),
                tweet['user']['name'], tweet['user']['screen_name']))
            for line in tweet['full_text'].split('\n'):
                if len(line.strip()) > 0:
                    message(u'   {}'.format(line))
        else:
            message(u'{} - {} (@{}) on Twitter: "{}"'.format(web.try_shorten(match.group(0)),
                tweet['user']['name'], tweet['user']['screen_name'], tweet['full_text'].replace('\n', ' | ')))
    except:
        message("{} - Twitter".format(web.try_shorten(match.group(0))))

