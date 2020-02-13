import math
import string
from datetime import datetime

from sqlalchemy import Column, String

from cloudbot import hook
from cloudbot.bot import bot
from cloudbot.util import database, http, web

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


def api_request(method, **params):
    api_key = bot.config.get_api_key("lastfm")
    params.update({"method": method, "api_key": api_key})

    try:
        data = http.get_json(api_url, params=params)
    except:
        return None, "LastFM API error, please try again in a few minutes."

    if 'error' in data:
        return data, "Error: {}.".format(data["message"])

    return data, None


def get_tags(method, artist, **params):
    tag_list = []
    tags, err = api_request(method +".getTopTags", artist=artist, autocorrect=1, **params)
    if err:
        return err

    # if artist doesn't exist return no tags
    if tags.get("error") == 6:
        return "no tags"

    blacklist = ["seen live"]
    tag_list = [tag['name'].lower() for tag in tags['toptags']['tag']
        if tag['name'].lower() not in blacklist][:4]

    return ', '.join(tag_list) if tag_list else 'no tags'


def get_similar_artists(artist):
    artist_list = []
    similar, err = api_request('artist.getsimilar', artist=artist, autocorrect=1)
    if err:
        return err

    # check it's a list
    if isinstance(similar['similarartists']['artist'], list):
        for item in similar['similarartists']['artist']:
            artist_list.append(item['name'])

    artist_list = artist_list[:4]

    return ', '.join(artist_list) if artist_list else 'No similar artists'


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
    artist, err = api_request("artist.getInfo", artist=artist, autocorrect=1, **params)
    if err:
        return err

    return artist


def get_account(nick, text=None):
    """looks in last_cache for the lastfm account name"""
    return last_cache.get(nick.lower(), text)


def check_key_and_user(db, nick, text=None, save=True):
    api_key = bot.config.get_api_key("lastfm")
    if not api_key:
        return None, "Error: No API key set."

    if text and save:
        if get_account(nick):
            lfmuser = db.query(lfmusers) \
                .filter(lfmusers.nick == nick.lower()) \
                .first()

            lfmuser.acc = text
            db.commit()
        else:
            lfmuser = lfmusers(nick.lower(), text)
            db.add(lfmuser)
            db.commit()

        load_cache(db)

    user = get_account(nick)

    if not user:
        return None, "No Last.FM username specified and no Last.FM username is set in the database."

    return user, None


@hook.command("nowplaying", "np", autohelp=False)
def nowplaying(text, nick, message, db):
    """[user] - displays the now playing (or last played) track of the LastFM user."""
    user, err = check_key_and_user(db, nick, text)
    if err:
        return err

    data, err = api_request('user.getrecenttracks', user=user, limit=1)
    if err:
        return err

    if 'track' not in data['recenttracks'] or not data['recenttracks']['track']:
        return "No recent tracks for user \"{}\" found.".format(user)

    tracks = data["recenttracks"]["track"]

    if isinstance(tracks, list):
        track = tracks[0]

        if "@attr" in track and "nowplaying" in track["@attr"] and track["@attr"]["nowplaying"] == "true":
            status = 'is listening to'
            ending = '.'
        else:
            status = 'last listened to'
            time_listened = datetime.fromtimestamp(int(track["date"]["uts"]))
            ending = ' ({})'.format(time_listened.strftime("%-d %b %Y %-I:%M"))
    else:
        return "Error: Could not parse track listing"

    title = track["name"]
    album = track["album"]["#text"]
    artist = track["artist"]["#text"]

    playcount = get_user_plays(artist, title, user)
    tags = get_tags("track", artist, track=title)
    if tags == "no tags":
        tags = get_tags("artist", artist)

    out = '\x02{}\x0f {} "\x02{}\x0f"'.format(user, status, title)
    if artist:
        out += " by \x02{}\x0f".format(artist)
    if album:
        out += " from the album \x02{}\x0f".format(album)

    out += " ({})".format(tags)
    out += ending

    if playcount:
        out += " [playcount: {}]".format(playcount)
    else:
        out += " [playcount: 0]"

    message(out)


@hook.command(autohelp=False)
def lfmuser(text, nick, message, db):
    """[user] - Gets a LastFM user's data."""
    user, err = check_key_and_user(db, nick, text)
    if err:
        return err

    data, err = api_request("user.getinfo", user=user, limit=5)
    if err:
        return err

    registered = (datetime.utcfromtimestamp(int(data['user']['registered']['unixtime']) + .1) -
        (datetime.utcnow() - datetime.now())).strftime("%d %b %Y")
    message(u"\x02{realname}\x0F (\x02{name}\x0F) has been a member since \x02{}\x0F and has " \
    "\x02{playcount}\x0f scrobbles.".format(registered, **data['user']))


@hook.command
def similar(text, message):
    """<artist> - Gets similar artists via Last.FM."""
    api_key = bot.config.get_api_key("lastfm")
    if not api_key:
        return "Error: No API key set."

    similar = get_similar_artists(text)

    message(f"Artists similar to \"\x02{text}\x0f\": {similar}")


@hook.command('tags', 'genres')
def tags(text, message):
    """<artist> - Gets genres for artist via Last.FM."""
    api_key = bot.config.get_api_key("lastfm")
    if not api_key:
        return "Error: No API key set."

    tags = get_tags("artist", text)

    message(f"Tags for \"\x02{text}\x0f\": {tags}")


@hook.command("plays")
def getplays(text, nick, message, db):
    """<artist> - Displays the current user's playcount for <artist>. You must have your username saved."""
    user, err = check_key_and_user(db, nick)
    if err:
        return err

    artist_info = get_artist_info(text, user)

    if 'error' in artist_info:
        return 'No such artist.'

    if 'userplaycount' not in artist_info['artist']['stats']:
        return f'{user} has never listened to {text}.'

    playcount = artist_info['artist']['stats']['userplaycount']

    message(f'{user} has {playcount} plays for {text}.')


@hook.command("band")
def getbandinfo(text, message):
    """<artist> - Displays information about the specified artist."""
    api_key = bot.config.get_api_key("lastfm")
    if not api_key:
        return "Error: No API key set."

    artist = get_artist_info(text)

    if 'error' in artist:
        return 'No such artist.'

    a = artist['artist']
    similar = get_similar_artists(text)
    tags = get_tags("artist", text)

    message("{} has {:,} plays and {:,} listeners. Similar artists include {}. Tags: {}.".format(
        text, int(a['stats']['playcount']), int(a['stats']['listeners']), similar, tags))


@hook.command(autohelp=False)
def toptrack(text, nick, message, db):
    """[period] - Grabs a list of the top tracks for the current user. You must have your username saved."""
    username, err = check_key_and_user(db, nick)
    if err:
        return err

    params = {}
    if text:
        params['period'] = text

    data, err = api_request("user.gettoptracks", user=username, limit=5, **params)
    if err:
        return err

    tracks = ['"{name}" by {artist[name]} ({playcount})'.format(**track)
        for track in data["toptracks"]["track"][:5]]

    message("{}'s top tracks: {}".format(username, ', '.join(tracks) or 'None'))


@hook.command(autohelp=False)
def topartists(text, nick, message, db):
    """[period] - Grabs a list of the top artists for the current user. You must have your username saved."""
    username, err = check_key_and_user(db, nick)
    if err:
        return err

    params = {}
    if text:
        params['period'] = text

    data, err = api_request("user.gettopartists", user=username, limit=5, **params)
    if err:
        return err

    artists = ["{name} ({playcount})".format(**artist)
        for artist in data["topartists"]["artist"][:5]]

    return "{}'s top artists: {}".format(username, ', '.join(artists) or 'None')

