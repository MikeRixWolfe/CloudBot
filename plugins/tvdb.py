from datetime import datetime
from json import dumps

from cloudbot import hook
from cloudbot.bot import bot
from cloudbot.util import http


base_url = "https://api.thetvdb.com"
login_url = base_url + "/login"
search_url = base_url + "/search/series"
series_url = base_url + "/series/{}"
episodes_url = series_url + "/episodes"


def get_token(api_key):
	return http.get_json("https://api.thetvdb.com/login", headers={'Content-Type':'application/json'},
		get_method='POST', data=dumps(api_key))['token']


def get_series_info(token, seriesname):
	head = {'Authorization': 'Bearer ' + token }

	params={'name': http.quote(seriesname)}
	series = http.get_json(search_url, headers=head, params=params)['data']
	_series = [s for s in series if s['network'] is not None]

	if len(_series) > 0:
		seriesid = _series[0]['id']
	else:
		seriesid = series[0]['id']

	return http.get_json(series_url.format(seriesid), headers=head)['data']


def get_series_eps(token, seriesid):
	head = {'Authorization': 'Bearer ' + token }

	episodes = http.get_json(episodes_url.format(seriesid), headers=head)

	if episodes['links']['last'] > 1:
		params = {'page': episodes['links']['last']}
		episodes = http.get_json(episodes_url.format(seriesid), headers=head)

	return episodes['data']


@hook.command
def tvnext(text, message):
	"""tvnext <series> - Get the next episode of <series>."""
	api_key = bot.config.get_api_key("tvdb")
	if not api_key:
		return "This command requires a TVDB API key."

	token = get_token(api_key)

	try:
		info = get_series_info(token, text)
	except:
		return "Series not found."

	eps = get_series_eps(token, info['id'])

	info['year'] = info.get('firstAired', '')[:4]
	info['network'] = info.get('network') or 'Unavailable'
	nextep = list(filter(lambda x: datetime.strptime(x.get('firstAired') or '1969-12-31','%Y-%m-%d') > datetime.now(), eps))

	if len(nextep) >= 1:
		nextep = min(nextep, key=lambda x: (x['airedSeason']*100)+x['airedEpisodeNumber'])

	if nextep:
		info.update(nextep)
		info['overview'] = info['overview'] or 'No description available'

		message('"{seriesName}" ({network} {year}) next episode airs {firstAired} at {airsTime} Eastern. S{airedSeason}E{airedEpisodeNumber} "{episodeName}": {overview}'.format(**info))
	elif info['status'] == 'Ended':
		message('{seriesName} ({network} {year}) has ended.'.format(**info))
	else:
		message('{seriesName} ({network} {year}) has no scheduled episodes. Show status: {status}'.format(**info))


@hook.command
def tvlast(text, message):
	"""tvlast <series> - Gets the most recently aired episode of <series>."""
	api_key = bot.config.get_api_key("tvdb")
	if not api_key:
		return "This command requires a TVDB API key."

	token = get_token(api_key)

	try:
		info = get_series_info(token, text)
	except:
		return "Series not found."

	eps = get_series_eps(token, info['id'])

	info['year'] = info['firstAired'][:4]
	info['network'] = info['network'] or 'Unavailable'
	lastep = max(eps, key=lambda x: (x['airedSeason']*100)+x['airedEpisodeNumber'])

	if len(eps) >= 1:
		info.update(lastep)
		info['overview'] = info['overview'] or 'No description available'

		message('"{seriesName}" ({network} {year}) last aired {firstAired} at {airsTime} Eastern. S{airedSeason}E{airedEpisodeNumber} "{episodeName}": {overview}'.format(**info))
	else:
		message('{seriesName} ({network} {year}) has yet to air an episode. Show status: {status}'.format(**info))
