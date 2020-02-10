import math
from datetime import datetime
from sqlalchemy import Table, Column, PrimaryKeyConstraint, String
from cloudbot import hook
from cloudbot.bot import bot
from cloudbot.util import colors, database, http, web


geo_url = 'https://maps.googleapis.com/maps/api/geocode/json'
weather_url = 'https://api.darksky.net/forecast/{}/{},{}'

table = Table(
    "weather",
    database.metadata,
    Column('nick', String),
    Column('loc', String),
    PrimaryKeyConstraint('nick')
)

location_cache = []

BEARINGS = ['N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE',
            'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW']

NUM_BEARINGS = len(BEARINGS)
MAX_DEGREES = 360
BEARING_SECTION = MAX_DEGREES / NUM_BEARINGS
BEARING_RANGE = BEARING_SECTION / 2


def strftime(time):
    return datetime.fromtimestamp(time).strftime("%p %A").replace('AM', 'early').replace('PM', 'late')


def add_location(nick, location, db):
    test = dict(location_cache)
    location = str(location)
    if nick.lower() in test:
        db.execute(table.update().values(loc=location.lower()).where(table.c.nick == nick.lower()))
        db.commit()
        load_cache(db)
    else:
        db.execute(table.insert().values(nick=nick.lower(), loc=location.lower()))
        db.commit()
        load_cache(db)


def get_location(nick):
    location = [row[1] for row in location_cache if nick.lower() == row[0]]
    if not location:
        return

    location = location[0]
    return location


def geocode(text):
    api_key = bot.config.get_api_key("google").get('access', None)
    if not api_key:
        raise Exception("This command requires a Google Developers Console API key.")

    bias = bot.config.get('region_bias_cc')

    if bias:
        params = {'key': api_key, 'address': text, 'region': bias}
    else:
        params = {'key': api_key, 'address': text}
    data = http.get_json(geo_url, params=params)

    return data['results'][0]

def get_weather(text, nick, reply, message, notice_doc, db):
    api_key = bot.config.get_api_key("darksky")
    if not api_key:
        raise Exception("This command requires a DarkSky API key.")

    if not text:
        location = get_location(nick)
        if not location:
            notice_doc()
            return None, None
    else:
        location = text
        add_location(nick, location, db)

    try:
        location_data = geocode(location)
    except:
        raise Exception("Google Geocoding API error, please try again in a few minutes.")

    try:
        weather_data = http.get_json(weather_url.format(api_key,
            location_data['geometry']['location']['lat'],
            location_data['geometry']['location']['lng']))
    except:
        raise Exception("DarkSky API error, please try again in a few minutes.")

    return location_data, weather_data


@hook.on_start
def load_cache(db):
    new_cache = []
    for row in db.execute(table.select()):
        nick = row["nick"]
        location = row["loc"]
        new_cache.append((nick, location))

    location_cache.clear()
    location_cache.extend(new_cache)


@hook.command("weather", "w", autohelp=False)
def weather(text, nick, reply, message, notice_doc, db):
    """<location> - Gets weather data for <location>."""
    try:
        geo, weather = get_weather(text, nick, reply, message, notice_doc, db)
    except Exception as e:
        return e

    try:
        if geo and weather:
            bearing = float(weather['currently']['windBearing'])
            direction = BEARINGS[math.floor(NUM_BEARINGS * (((bearing + BEARING_RANGE) % MAX_DEGREES) / MAX_DEGREES))]
            alerts = ', '.join(['\x02{}\x0F until \x02{}\x0F'.format(a['title'], strftime(a['expires'])) for a in weather.get('alerts', [])])

            message(u"\x02{location}\x0F: {currently[temperature]:.0f}\u00b0F " \
                u"and {currently[summary]}, feels like {currently[apparentTemperature]:.0f}\u00b0F, " \
                u"wind at {currently[windSpeed]:.0f} ({currently[windGust]:.0f} gust) MPH {direction}, " \
                u"humidity at {currently[humidity]:.0%}. {alert}".format(direction=direction,
                location=geo['formatted_address'], alert=alerts, **weather))
    except:
        return "Error: unable to find weather data for location."


@hook.command("forecast", "fc", autohelp=False)
def forecast(text, nick, reply, message, notice_doc, db):
    """<location> - Gets forecast data for <location>."""
    try:
        geo, weather = get_weather(text, nick, reply, message, notice_doc, db)
    except Exception as e:
        return e

    try:
        if geo and weather:
            for day in weather['daily']['data']:
                day['day'] = datetime.fromtimestamp(day['time']).strftime("%A")
            message(u"\x02{location}\x0F: ".format(location=geo['formatted_address']) +
                u"; ".join([u"\x02{day}\x0F: L {temperatureLow:.0f}\u00b0F, H {temperatureHigh:.0f}\u00b0F, {summary}".format(**day)
                for day in weather['daily']['data'][0:5]]))
    except:
        return "Error: unable to find weather data for location."


@hook.command("hourly", "h", autohelp=False)
def hourly(text, nick, reply, message, notice_doc, db):
    """<location> - Gets hourly weather data for <location>."""
    try:
        geo, weather = get_weather(text, nick, reply, message, notice_doc, db)
    except Exception as e:
        return e

    try:
        if geo and weather:
            for hour in weather['hourly']['data']:
                hour['hour'] = datetime.fromtimestamp(hour['time']).strftime("%-I%p")
            message(u"\x02{location}\x0F: ".format(location=geo['formatted_address']) +
                u"; ".join([u"\x02{hour}\x0F: {temperature:.0f}\u00b0F ({apparentTemperature:.0f}\u00b0F feel), {summary}".format(**hour)
                for hour in weather['hourly']['data'][0:10]]))
    except:
        return "Error: unable to find weather data for location."

