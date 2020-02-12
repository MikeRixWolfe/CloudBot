import math
import string
from datetime import datetime

from sqlalchemy import Column, String

from cloudbot import hook
from cloudbot.bot import bot
from cloudbot.util import database, http, timeformat, web

api_url = "http://ws.audioscrobbler.com/2.0/?format=json"

class lfmusers(database.base):
    __tablename__ = 'lastfm'
    __table_args__ = {'extend_existing': True}

    nick = Column(String, primary_key=True)
    acc = Column(String)

    def __init__(self, nick, acc):
        self.nick = nick
        self.acc = acc

database.metadata.create_all(database.engine)
last_cache = {}


@hook.on_start()
def load_cache(db):
    new_cache = {}
    for row in db.query(lfmusers).all():
        new_cache[row.nick] = row.acc

    last_cache.clear()
    last_cache.update(new_cache)


def get_account(nick, text=None):
    """looks in last_cache for the lastfm account name"""
    return last_cache.get(nick.lower(), text)


def api_request(method, **params):
    api_key = bot.config.get_api_key("lastfm")
    params.update({"method": method, "api_key": api_key})
    data = http.get_json(api_url, params=params)

    if 'error' in data:
        return data, "Error: {}.".format(data["message"])

    return data, None


def get_tags(artist, **params):
    tag_list = []
    tags, _ = api_request("artist.getTopTags", artist=artist, autocorrect=1, **params)

    # if artist doesn't exist return no tags
    if tags.get("error") == 6:
        return "no tags"

    blacklist = ["seen live"]
    tag_list = [tag['name'].lower() for tag in tags['toptags']['tag'] if tag['name'].lower() not in blacklist][:4]

    return ', '.join(tag_list) if tag_list else 'no tags'


def get_similar_artists(artist):
    artist_list = []
    similar, _ = api_request('artist.getsimilar', artist=artist, autocorrect=1)

    # check it's a list
    if isinstance(similar['similarartists']['artist'], list):
        for item in similar['similarartists']['artist']:
            artist_list.append(item['name'])

    artist_list = artist_list[:4]

    return ', '.join(artist_list) if artist_list else 'no similar artists'


def get_user_plays(artist, track, user):
    track_info, err = api_request("track.getInfo", artist=artist, track=track, username=user)
    if err and not track_info:
        return err

    # if track doesn't exist return 0 playcount
    if track_info.get("error") == 6:
        return 0

    return track_info['track'].get('userplaycount')


def get_artist_info(artist, user=''):
    params = {}
    if user:
        params['username'] = user
    artist, _ = api_request("artist.getInfo", artist=artist, autocorrect=1, **params)
    return artist


def check_key_and_user(nick, text, lookup=False):
    api_key = bot.config.get_api_key("lastfm")
    if not api_key:
        return None, "Error: No API key set.."

    if text:
        if lookup:
            username = get_account(text, text)
        else:
            username = text
    else:
        username = get_account(nick)

    if not username:
        return None, "No last.fm username specified and no last.fm username is set in the database."

    return username, None


def get_top_artists(text, nick, period=None, limit=10):
    username, err = check_key_and_user(nick, text, True)
    if err:
        return err

    params = {}
    if period:
        params['period'] = period

    data, err = api_request("user.gettopartists", user=username, limit=limit, **params)
    if err:
        return err

    artists = ["{name} ({playcount})".format(**artist)
        for artist in data["topartists"]["artist"][:limit]]

    return "{}'s top artists: {}".format(username, ', '.join(artists) or 'None')


@hook.command("nowplaying", "np", autohelp=False)
def nowplaying(text, nick, message, db, notice_doc):
    """[user] [dontsave] - displays the now playing (or last played) track of LastFM user [user]"""
    api_key = bot.config.get_api_key("lastfm")
    if not api_key:
        return "Error: No API key set."

    # check if the user asked us not to save his details
    dontsave = text.endswith(" dontsave")
    if dontsave:
        user = text[:-9].strip().lower()
    else:
        user = text

    if not user:
        user = get_account(nick)
        if not user:
            notice_doc()
            return

    try:
        response, err = api_request('user.getrecenttracks', user=user, limit=1)
    except:
        return "LastFM API error, please try again in a few minutes."

    if err:
        return err

    if 'track' not in response['recenttracks'] or not response['recenttracks']['track']:
        return "No recent tracks for user \"{}\" found.".format(user)

    tracks = response["recenttracks"]["track"]

    if isinstance(tracks, list):
        track = tracks[0]

        if "@attr" in track and "nowplaying" in track["@attr"] and track["@attr"]["nowplaying"] == "true":
            status = 'is listening to'
            ending = '.'
        else:
            status = 'last listened to'
            time_listened = datetime.fromtimestamp(int(track["date"]["uts"]))
            time_since = timeformat.time_since(time_listened)
            ending = ' ({} ago)'.format(time_since)
    else:
        return "Error: Could not parse track listing"

    title = track["name"]
    album = track["album"]["#text"]
    artist = track["artist"]["#text"]

    out = '\x02{}\x0f {} "\x02{}\x0f"'.format(user, status, title)
    if artist:
        out += " by \x02{}\x0f".format(artist)
    if album:
        out += " on \x02{}\x0f".format(album)

    # append ending based on what type it was
    out += ending

    if text and not dontsave:
        if get_account(nick):
            lfmuser = db.query(lfmusers) \
                .format(lfmusers.nick == nick.lower()) \
                .first()

            lfmuser.acc = user
            db.commit()
        else:
            lfmuser = lfmusers(nick.lower(), user)
            db.add(lfmuser)
            db.commit()

        load_cache(db)
    message(out)


@hook.command("plays")
def getplays(text, nick, message, notice_doc):
    """[artist] - displays the current user's playcount for [artist]. You must have your username saved."""
    api_key = bot.config.get_api_key("lastfm")
    if not api_key:
        return "Error: No API key set."

    user = get_account(nick)
    if not user:
        notice_doc()
        return

    artist_info = get_artist_info(text, user)

    if 'error' in artist_info:
        return 'No such artist.'

    if 'userplaycount' not in artist_info['artist']['stats']:
        return f'{user} has never listened to {text}.'

    playcount = artist_info['artist']['stats']['userplaycount']

    message(f'{user} has {playcount} plays for {text}.')


@hook.command("band")
def getbandinfo(text, message):
    """[artist] - displays information about [artist]."""
    api_key = bot.config.get_api_key("lastfm")
    if not api_key:
        return "Error: No API key set."

    artist = get_artist_info(text)

    if 'error' in artist:
        return 'No such artist.'

    a = artist['artist']
    similar = get_similar_artists(text)
    tags = get_tags(text)

    out = "{} has {:,} plays and {:,} listeners.".format(text, int(a['stats']['playcount']),
                                                         int(a['stats']['listeners']))
    out += " Similar artists include {}. Tags: {}.".format(similar, tags)

    message(out)


@hook.command(autohelp=False)
def toptrack(text, nick, message):
    """[username] - Grabs a list of the top tracks for a last.fm username"""
    username, err = check_key_and_user(nick, text, True)
    if err:
        return err

    data, err = api_request("user.gettoptracks", user=username, limit=5)
    if err:
        return err
    print(data)
    tracks = ['"{name}" by {artist[name]} ({playcount})'.format(**track)
        for track in data["toptracks"]["track"][:5]]

    message("{}'s top tracks: {}".format(username, ', '.join(tracks) or 'None'))


@hook.command(autohelp=False)
def topartists(text, nick, message):
    """[username] - Grabs a list of the top artists for a last.fm username."""
    message(get_top_artists(text, nick))


@hook.command(autohelp=False)
def topweek(text, nick, message):
    """[username] - Grabs a list of the top artists in the last week for a last.fm username."""
    message(get_top_artists(text, nick, '7day'))


@hook.command(autohelp=False)
def topmonth(text, nick, message):
    """[username] - Grabs a list of the top artists in the last month for a last.fm username."""
    message(get_top_artists(text, nick, '1month'))


@hook.command(autohelp=False)
def topyear(text, nick, message):
    """[username] - Grabs a list of the top artists in the last year for a last.fm username."""
    message(get_top_artists(text, nick, '1year'))

