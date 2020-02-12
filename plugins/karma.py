import operator
import re
from collections import defaultdict

import sqlalchemy
from sqlalchemy import String, Column, Integer

from cloudbot import hook
from cloudbot.util import database

karmaplus_re = re.compile(r'(.*)\+\+')
karmaminus_re = re.compile(r'(.*)--')

class karma(database.base):
    __tablename__ = 'karma'
    __table_args__ = {'extend_existing': True}

    chan = Column(String, primary_key=True)
    thing = Column(String, primary_key=True)
    nick = Column(String)
    score = Column(Integer)

    def __init__(self, chan, thing, nick, score):
        self.chan = chan
        self.thing = thing
        self.nick = nick
        self.score = score


def update_score(nick, chan, thing, score, db):
    if nick.casefold() == chan.casefold():
        return

    _karma = db.query(karma) \
        .filter(karma.chan == chan) \
        .filter(karma.nick == nick.lower()) \
        .filter(karma.thing == thing.lower()) \
        .all()

    if _karma:
        _karma.score += score
    else:
        _karma = karma(chan, thing.lower(), nick.lower(), score)
        db.add(_karma)

    db.commit()


@hook.regex(karmaplus_re)
def increment(match, nick, chan, db):
    update_score(match.group(1), nick, chan, 1, db)


@hook.regex(karmaminus_re)
def decrement(match, nick, chan, db):
    update_score(match.group(1), nick, chan, -1, db)


@hook.command(autohelp=False)
def karma(text, chan, message, db):
    """<thing> - will print the total points for <thing> in the channel."""
    try:
        text = [t for t in text.split(' ') if t]
        text.remove('-g')
        g = True
        text = ' '.join(text)
    except:
        g = False
        text = ' '.join(text)

    if g:
        data = db.query(karma) \
             .filter(karma.nick == nick.lower()) \
             .filter(karma.thing == text.lower()) \
             .all()
    else:
        data = db.query(karma) \
             .filter(karma.chan == chan) \
             .filter(karma.nick == nick.lower()) \
             .filter(karma.thing == text.lower()) \
             .all()

    if data:
        print(data)
        score = 0
        pos = 0
        neg = 0
        for k in data:
            if int(k[0]) < 0:
                neg += int(k[0])
            else:
                pos += int(k[0])
            score += int(k[0])
        if g:
            message(f"{text} has a total score of {score} (+{pos}/{neg}) across all channels I know about.")
        else:
            message(f"{text} has a total score of {score} (+{pos}/{neg}) in {chan}.")
    else:
        return f"I couldn't find {text} in the database."

