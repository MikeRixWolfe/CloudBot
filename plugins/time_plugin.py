import datetime
import re
import time

from cloudbot import hook
from cloudbot.bot import bot
from cloudbot.util import http

# Define some constants
base_url = 'https://maps.googleapis.com/maps/api/'
geocode_api = base_url + 'geocode/json'
timezone_api = base_url + 'timezone/json'

# Change this to a ccTLD code (eg. uk, nz) to make results more targeted towards that specific country.
# <https://developers.google.com/maps/documentation/geocoding/#RegionCodes>


def check_status(status, api):
    """ A little helper function that checks an API error code and returns a nice message.
        Returns None if no errors found """
    if status == 'REQUEST_DENIED':
        return 'The ' + api + ' API is off in the Google Developers Console.'

    if status == 'ZERO_RESULTS':
        return 'No results found.'

    if status == 'OVER_QUERY_LIMIT':
        return 'The ' + api + ' API quota has run out.'

    if status == 'UNKNOWN_ERROR':
        return 'Unknown Error.'

    if status == 'INVALID_REQUEST':
        return 'Invalid Request.'

    if status == 'OK':
        return None

    # !!!
    return 'Unknown Demons.'


@hook.command("time")
def time_command(text, reply):
    """<location> - Gets the current time in <location>."""
    api_key = bot.config.get_api_key("google").get('access')
    if not api_key:
        return "This command requires a Google Developers Console API key."

    if text.lower().startswith("utc") or text.lower().startswith("gmt"):
        timezone = text.strip()
        pattern = re.compile(r"utc|gmt|[:+]")
        utcoffset = [x for x in pattern.split(text.lower()) if x]
        if len(utcoffset) > 2:
            return "Please specify a valid UTC/GMT format Example: UTC-4, UTC+7 GMT7"
        if len(utcoffset) == 1:
            utcoffset.append('0')
        if len(utcoffset) == 2:
            try:
                offset = datetime.timedelta(hours=int(utcoffset[0]), minutes=int(utcoffset[1]))
            except Exception:
                reply("Sorry I could not parse the UTC format you entered. Example UTC7 or UTC-4")
                raise
            curtime = datetime.datetime.utcnow()
            tztime = curtime + offset
            formatted_time = datetime.datetime.strftime(tztime, '%I:%M %p, %A, %B %d, %Y')
            return "\x02{}\x02 ({})".format(formatted_time, timezone)

    # Use the Geocoding API to get co-ordinates from the input
    params = {"address": text, "key": api_key}
    bias = bot.config.get('region_bias_cc')
    if bias:
        params['region'] = bias

    json = http.get_json(geocode_api, params=params)

    error = check_status(json['status'], "geocoding")
    if error:
        return error

    result = json['results'][0]

    location_name = result['formatted_address']
    location = result['geometry']['location']

    # Now we have the co-ordinates, we use the Timezone API to get the timezone
    formatted_location = "{lat},{lng}".format(**location)

    epoch = time.time()

    params = {"location": formatted_location, "timestamp": epoch, "key": api_key}
    json = http.get_json(timezone_api, params=params)

    error = check_status(json['status'], "timezone")
    if error:
        return error

    # Work out the current time
    offset = json['rawOffset'] + json['dstOffset']

    # I'm telling the time module to parse the data as GMT, but whatever, it doesn't matter
    # what the time module thinks the timezone is. I just need dumb time formatting here.
    raw_time = time.gmtime(epoch + offset)
    formatted_time = time.strftime('%I:%M %p, %A, %B %d, %Y', raw_time)

    timezone = json['timeZoneName']

    return "\x02{}\x02 - {} ({})".format(formatted_time, location_name, timezone)

