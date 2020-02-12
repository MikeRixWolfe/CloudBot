import random
import re
import sqlalchemy
import time

from sqlalchemy import Column, String, Integer, Boolean
from sqlalchemy.exc import IntegrityError
from sqlalchemy.types import REAL

from cloudbot import hook
from cloudbot.util import database, formatting

class quotes(database.base):
    __tablename__ = 'quotes'
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True)
    nick = Column(String)
    quote = Column(String)
    time = Column(REAL)
    active = Column(Boolean, default=True)

    def __init__(self, nick, quote, time):
        self.nick = nick
        self.quote = quote
        self.time = time


def format_quote(q):
    """Returns a formatted string of a quote"""
    uts = time.strftime("%B %Y", time.localtime(q.time))
    return f'Quote #{q.id}: "{q.quote}" set by {q.nick} in {uts}'


@hook.command('q', 'quote')
def quote(text, nick, message, db):
    """<text> - Adds a quote."""
    try:
        quote = quotes(nick, text, time.time())
        db.add(quote)
        db.commit()
    except IntegrityError:
        message("Message already stored, doing nothing.")
    message("Quote added.")


@hook.command('randomquote', 'randquote', 'rq', autohelp=False)
def randomquote(text, message, db):
    """[text] - Gets a random quote."""

    if text:
        data = db.query(quotes) \
            .filter(quotes.active == True) \
            .filter(quotes.quote.like(f"%{text}%")) \
            .order_by(sqlalchemy.func.random()) \
            .limit(1).first()
    else:
        data = db.query(quotes) \
            .filter(quotes.active == True) \
            .order_by(sqlalchemy.func.random()) \
            .limit(1).first()

    if data:
        message(format_quote(data))
    else:
        return "None found."


@hook.command
def getquote(text, message, db):
    """<n> - Gets the <n>th quote."""
    data = db.query(quotes) \
        .filter(quotes.id == int(text)) \
        .limit(1).first()

    if data:
        message(format_quote(data))
    else:
        return f"Quote #{text} was not found."


@hook.command
def searchquote(text, message, db):
    """<text> - Returns IDs for quotes matching <text>."""
    data = db.query(quotes) \
        .filter(quotes.quote.like(f"%{text}%")) \
        .all()

    if data:
        message(formatting.truncate_str("Quotes: {}".format(
            ', '.join([str(d.id) for d in data])), 350))
    else:
        return "None found."


@hook.command
def delquote(text, db):
    """<n> - Deletes the <n>th quote."""
    data = db.query(quotes) \
        .filter(quotes.id == int(text)) \
        .filter(quotes.active == True) \
        .first()

    if data:
        data.active = False
        db.commit()
        return f"Quote #{text} deleted."
    else:
        return f"Quote #{text} was not found."


@hook.command
def restorequote(text, db):
    """<n> - Restores the <n>th quote."""
    data = db.query(quotes) \
        .filter(quotes.id == int(text)) \
        .filter(quotes.active == False) \
        .first()

    if data:
        data.active = True
        db.commit()
        return f"Quote #{text} restored."
    else:
        return f"Quote #{text} was not found."

