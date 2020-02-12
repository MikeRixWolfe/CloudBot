import os
import re
import subprocess

from cloudbot import hook


unix_ping_regex = re.compile(r"(\d+.\d+)/(\d+.\d+)/(\d+.\d+)/(\d+.\d+)")


@hook.command
def ping(text):
    """<host> - Pings an IP address or domain."""
    try:
        pingcmd = subprocess.check_output(["ping", "-c", "1", text.split()[0]]).decode("utf-8")
    except subprocess.CalledProcessError:
        return "Could not ping host."

    if re.search("(?:not find host|timed out|unknown host)", pingcmd, re.I):
        return "Could not ping host."

    return pingcmd.split("\n")[1]
