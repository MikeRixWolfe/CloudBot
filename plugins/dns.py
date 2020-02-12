import re
import socket

from cloudbot import hook


@hook.command
def dns(text):
    """<ip|domain> - Resolves IP of Domain or vice versa."""
    try:
        socket.setdefaulttimeout(15)
        if not re.match(r'\d+\.\d+\.\d+\.\d+', text):
            out = socket.gethostbyname(text)
        else:
            out = socket.gethostbyaddr(text)[0]
        return f"{text} resolves to {out}"
    except:
        return f"I could not find {text}"

