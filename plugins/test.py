from cloudbot import hook
from cloudbot.util import web


@hook.command(autohelp=False)
async def test(text, nick, message):
    """[text] - Tests your hilight window."""
    if text:
        message(f'Hello {nick}; "{text}"')
    else:
        message(f'Hello {nick}')

