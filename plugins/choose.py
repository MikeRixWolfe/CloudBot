import random
import re
from cloudbot import hook


@hook.command()
async def choose(text):
    """<choice1>, <choice2>, ... <choice n> - Makes a decision."""
    c = re.findall(r'([^,]+)', text)
    if len(c) == 1:
        c = re.findall(r'(\S+)', text)
    c = set(x.strip() for x in c)  # prevent weighting, normalize
    if len(c) == 1:
        return "Looks like you've already made that decision."
    x = random.choice(list(c))
    if x == '4':
        return 'http://imgs.xkcd.com/comics/random_number.png'  # heh
    return x

