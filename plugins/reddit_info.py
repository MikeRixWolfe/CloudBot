import random
import re
from datetime import datetime

from cloudbot import hook
from cloudbot.util import colors, http, timeformat, formatting, web

user_re = re.compile(r'^(?:/?(?:u(?:ser)?/)?)?(?P<name>.+?)/?$', re.IGNORECASE)
sub_re = re.compile(r'^(?:/?(?:r/)?)?(?P<name>.+?)/?$', re.IGNORECASE)

subreddit_url = "http://reddit.com/r/{}/"
short_url = "https://redd.it/{}"
post_url = "https://reddit.com/comments/{}.json"

post_re = re.compile(r"https?:\/\/(?:www\.|old\.)?reddit\.com\/(?:r\/[^\/]+\/comments\/([^\/]+)[^ ]+|[^ ]+)", re.I)


def get_sub(text):
    match = sub_re.match(text)
    if match:
        return match.group('name')


def format_output(item):
    """ takes a reddit post and returns a formatted string """
    item["title"] = formatting.truncate(item["title"], 70)
    item["link"] = short_url.format(item["id"])

    raw_time = datetime.fromtimestamp(int(item["created_utc"]))
    item["timesince"] = timeformat.time_since(raw_time, count=1, simple=True)

    item["comments"] = formatting.pluralize_auto(item["num_comments"], 'comment')
    item["points"] = formatting.pluralize_auto(item["score"], 'point')

    if item["over_18"]:
        item["warning"] = colors.parse("$(b, red)NSFW$(clear) ")
    else:
        item["warning"] = ""

    item["url"] = web.try_shorten(item["link"])

    return colors.parse("{url} - {warning}$(b){title} : {subreddit}$(b) - {comments}, {points}"
        " - $(b){author}$(b) {timesince} ago").format(**item)


@hook.regex(post_re, singlethread=True)
def reddit_post_url(match, message):
    post_id = match.group(1)

    try:
        data = http.get_json(post_url.format(post_id), timeout=2)
        item = data[0]["data"]["children"][0]["data"]
        message(format_output(item))
    except Exception as e:
        print(match.group(0))
        title = http.get_title(match.group(0))
        title = u' '.join(re.sub(u'\r|\n', u' ', title).split()).strip('| ')
        url = web.try_shorten(match.group(0))
        message(f"{url} - {title}")



@hook.command(autohelp=False, singlethread=True)
def reddit(text, reply):
    """[subreddit] [n] - gets a random post from <subreddit>, or gets the [n]th post in the subreddit"""
    id_num = None

    if text:
        # clean and split the input
        parts = text.lower().strip().split()
        sub = get_sub(parts.pop(0).strip())
        url = subreddit_url.format(sub)

        # find the requested post number (if any)
        if parts:
            try:
                id_num = int(parts[0]) - 1
            except ValueError:
                return "Invalid post number."
    else:
        url = "https://reddit.com"

    try:
        data = http.get_json(url + '.json')
    except Exception as e:
        reply("Error: " + str(e))
        raise

    data = data["data"]["children"]

    if not data:
        return "There do not appear to be any posts to show."

    # get the requested/random post
    if id_num is not None:
        try:
            item = data[id_num]
        except IndexError:
            length = len(data)
            return "Invalid post number. Number must be between 1 and {}.".format(length)
    else:
        item = random.choice(data)

    return format_output(item["data"])

