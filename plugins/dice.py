import random
import re

from cloudbot import hook

whitespace_re = re.compile(r'\s+')
valid_diceroll = r'^([+-]?(?:\d+|\d*d(?:\d+|F))(?:[+-](?:\d+|\d*d(?:\d+|F)))*)( .+)?$'
valid_diceroll_re = re.compile(valid_diceroll, re.I)
sign_re = re.compile(r'[+-]?(?:\d*d)?(?:\d+|F)', re.I)
split_re = re.compile(r'([\d+-]*)d?(F|\d*)', re.I)


def nrolls(count, n):
    "roll an n-sided die count times"
    if n == "F":
        return [random.randint(-1, 1) for x in range(min(count, 100))]
    if n < 2:  # it's a coin
        if count < 100:
            return [random.randint(0, 1) for x in range(count)]
        else:  # fake it
            return [int(random.normalvariate(.5 * count, (.75 * count) ** .5))]
    else:
        if count < 100:
            return [random.randint(1, n) for x in range(count)]
        else:  # fake it
            return [int(random.normalvariate(.5 * (1 + n) * count,
                                             (((n + 1) * (2 * n + 1) / 6. -
                                             (.5 * (1 + n)) ** 2) * count) ** .5))]


@hook.command
def roll(text):
    """<diceroll> - Simulates dicerolls, e.g. .dice 2d20-d5+4 roll 2 D20s, subtract 1D5, add 4."""

    try:  # if text is a re.match object...
        (text, desc) = text.groups()
    except AttributeError:
        try:
            (text, desc) = valid_diceroll_re.match(text).groups()
        except:
            return "Invalid diceroll"

    if "d" not in text:
        return

    spec = whitespace_re.sub('', text)
    if not valid_diceroll_re.match(spec):
        return "Invalid diceroll"
    groups = sign_re.findall(spec)

    total = 0
    rolls = []

    for roll in groups:
        count, side = split_re.match(roll).groups()
        count = int(count) if count not in " +-" else 1
        if side.upper() == "F":  # fudge dice are basically 1d3-2
            for fudge in nrolls(count, "F"):
                if fudge == 1:
                    rolls.append("\x033+\x0F")
                elif fudge == -1:
                    rolls.append("\x034-\x0F")
                else:
                    rolls.append("0")
                total += fudge
        elif side == "":
            total += count
        else:
            side = int(side)
            try:
                if count > 0:
                    dice = nrolls(count, side)
                    rolls += map(str, dice)
                    total += sum(dice)
                else:
                    dice = nrolls(-count, side)
                    rolls += [str(-x) for x in dice]
                    total -= sum(dice)
            except OverflowError:
                return "Thanks for overflowing a float, jerk >:["

    if desc:
        return "{}: {} ({}={})".format(desc.strip(), total, text, ", ".join(rolls))
    else:
        return "{} ({}={})".format(total, text, ", ".join(rolls))

