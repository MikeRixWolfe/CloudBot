import os
import platform
import time
from datetime import timedelta

try:
    import psutil
except ImportError:
    psutil = None

from cloudbot import hook
from cloudbot.util.filesize import size as format_bytes
import cloudbot


@hook.command(autohelp=False)
def about(text, conn, bot):
    """- Gives information about CloudBot. Use .about license for licensing information"""
    if text.lower() in ("license", "gpl", "source"):
        return "CloudBot Refresh is released under the GPL v3 license, get the source code " \
               "at {}".format(_get_repo_link(bot))

    return "{} is powered by CloudBot Refresh! ({}) - {}".format(
        conn.nick, cloudbot.__version__, _get_repo_link(bot)
    )


@hook.command(autohelp=False)
def system(message):
    """- Retrieves information about the host system."""

    # Get general system info
    sys_os = platform.platform()
    python_implementation = platform.python_implementation()
    python_version = platform.python_version()
    sys_architecture = '-'.join(platform.architecture())
    sys_cpu_count = platform.machine()

    message(
        "OS: \x02{}\x02, "
        "Python: \x02{} {}\x02, "
        "Architecture: \x02{}\x02 (\x02{}\x02)".format(
            sys_os,
            python_implementation,
            python_version,
            sys_architecture,
            sys_cpu_count
        )
    )

    if psutil:
        process = psutil.Process(os.getpid())

        # get the data we need using the Process we got
        cpu_usage = process.cpu_percent(1)
        thread_count = process.num_threads()
        memory_usage = format_bytes(process.memory_info()[0])
        uptime = timedelta(seconds=round(time.time() - process.create_time()))

        message(
            "Uptime: \x02{}\x02, "
            "Threads: \x02{}\x02, "
            "CPU Usage: \x02{}\x02, "
            "Memory Usage: \x02{}\x02".format(
                uptime,
                thread_count,
                cpu_usage,
                memory_usage
            )
        )

