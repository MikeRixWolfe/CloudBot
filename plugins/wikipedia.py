from cloudbot import hook
from cloudbot.util import http, web

search_api = u'http://en.wikipedia.org/w/api.php'
page_url = u'https://en.wikipedia.org/wiki/'


@hook.command
def wiki(text, message):
    """<phrase> - Gets first sentence of Wikipedia article on <phrase>."""
    try:
        params = { 'action': 'query', 'list': 'search',
                   'format': 'json', 'srsearch': http.quote(text) }
        search = http.get_json(search_api, params=params)
    except:
        return 'Error accessing Wikipedia API, please try again in a few minutes.'

    if len(search['query']['search']) == 0:
        return 'Your query returned no results, please check your textut and try again.'

    try:
        params = { 'format': 'json' , 'action': 'query' , 'prop': 'extracts',
                   'exintro': True, 'explaintext': True, 'exchars' : 425,
                   'redirects': 1, 'titles': search['query']['search'][0]['title'] }
        data = http.get_json(search_api, params=params)
    except:
        return 'Error accessing Wikipedia API, please try again in a few minutes.'


    data = data['query']['pages'][list(data['query']['pages'].keys())[0]]
    data['extract'] = data['extract'].strip('...').rsplit('.', 1)[0] + '.'
    message(u'{} - {}'.format(web.try_shorten(page_url + data['title']), data['extract']))

