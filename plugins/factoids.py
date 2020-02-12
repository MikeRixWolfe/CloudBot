import re

from collections import defaultdict
from sqlalchemy import Column, String

from cloudbot import hook
from cloudbot.util import database, formatting


remember_re = re.compile(r'^(?P<replace>no )?G2[:, ]+(?P<word>(?!\().+?(?!\()|\(.+\)) is (?P<append>also )?(?P<data>.+)$', re.I)
factoid_re = re.compile(r'^(?P<word>.+)\?$', re.I)


class factoids(database.base):
    __tablename__ = 'factoids'
    __table_args__ = {'extend_existing': True}

    word = Column(String, primary_key=True)
    chan = Column(String, primary_key=True)
    data = Column(String)

    def __init__(self, word, chan, data):
        self.word = word
        self.chan = chan
        self.data = data

database.metadata.create_all(database.engine)
factoid_cache = defaultdict({}.copy)


@hook.on_start()
def load_cache(db):
    new_cache = defaultdict({}.copy)
    for row in db.query(factoids).all():
        new_cache[row.chan][row.word] = row.data

    factoid_cache.clear()
    factoid_cache.update(new_cache)


def add_factoid(db, word, chan, data, nick):
    if word in factoid_cache[chan]:
        factoid = db.query(factoids) \
            .filter(factoids.chan == chan) \
            .filter(factoids.word.lower() == word.lower()) \
            .first()
        factoid.data = data
    else:
        factoid = factoids(word, chan, data)
        db.add(factoid)

    db.commit()
    load_cache(db)


def del_factoid(db, chan, word):
    factoid = db.query(factoids) \
        .filter(factoids.chan == chan) \
        .filter(factoids.word.lower() == word.lower()) \
        .first()

    if factoid:
        db.delete(factoid)
        db.commit()

    load_cache(db)


@hook.regex(remember_re)
def remember(match, nick, chan, db, message):
    match = match.groupdict()

    try:
        old_data = factoid_cache[chan][match['word']]
    except LookupError:
        old_data = None

    if old_data:
        if match.get('replace', False):
            data = match['data']
        elif match.get('append', False):
            data = f"{old_data} or {match['data']}"
        else:
            return f"But, {match['word']} is {old_data}"
    else:
        data = f"{match['data']}"

    add_factoid(db, match['word'], chan, data, nick)
    message(f"Ok {nick}")



@hook.command
def forget(text, chan, db, message):
    """<word> - Remove factoids with the specified names."""
    if text in factoid_cache[chan]:
        del_factoid(db, chan, text)
        message(f"I forgot {text}")


@hook.regex(factoid_re)
def factoid(match, chan, message, action):
    """<word> - shows what data is associated with <word>."""
    if match['word'] in factoid_cache[chan]:
        message(f"{match['word']} is {factoid_cache[chan][match['word']]}")


@hook.command("factoids", autohelp=False)
def list_factoids(chan, message):
    """- lists all available factoids."""
    message(formatting.truncate_str(", ".join(sorted(factoid_cache[chan].keys())), 400) or "None")

