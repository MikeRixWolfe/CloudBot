import socket

from cloudbot import hook
from cloudbot.util import http


@hook.command
def isup(text):
    """<site> - Checks if a site is up or not."""
    url = 'http://' + text if '://' not in text else text

    try:
        page = http.open(url)
        code = page.getcode()
    except http.HTTPError as e:
        code = e.code
    except socket.timeout as e:
        code = 'Socket Timeout'
    except Exception as e:
        code = 'DNS Not Resolved'

    if code == 200:
        return f"It's just you. {url} is \x02\x033up\x02\x0f."
    else:
        return f"It's not just you. {url} looks \x02\x034down\x02\x0f from here ({code})"

