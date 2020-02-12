from cloudbot import hook
from cloudbot.bot import bot
from cloudbot.util import http, web


@hook.command
def imdb(text):
    """<movie> [year] - Gets information about a movie from IMDb."""
    api_key = bot.config.get_api_key("omdb")
    if not api_key:
        return "This command requires an API key from omdb.com."

    year = ""
    if text.split()[-1].isdigit():
        text, year = ' '.join(text.split()[:-1]), text.split()[-1]

    try:
        content = http.get_json("http://www.omdbapi.com/", apikey=api_key, t=text, y=year, plot='short', r='json')
    except:
        return "OMDB API error, please try again in a few minutes."

    if content['Response'] == 'False':
        return content['Error']
    elif content['Response'] == 'True':
        content['URL'] = 'http://www.imdb.com/title/%(imdbID)s' % content

        out = '\x02{Title}\x02 ({Year}) ({Genre}): {Plot}'
        if content['Runtime'] != 'N/A':
            out += ' \x02{Runtime}\x02.'
        if content['imdbRating'] != 'N/A' and content['imdbVotes'] != 'N/A':
            out += ' \x02{imdbRating}/10\x02 with \x02{imdbVotes}\x02 votes. '
        out += web.try_shorten('{URL}'.format(**content))
        return out.format(**content)
    else:
        return "Error parsing movie information."
