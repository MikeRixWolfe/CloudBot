import re
from collections import defaultdict

from sqlalchemy import Column, String

from cloudbot import hook
from cloudbot.event import EventType
from cloudbot.util import database


class badwords(database.base):
	__tablename__ = 'badwords'
	__table_args__ = {'extend_existing': True}

	chan = Column(String, primary_key=True)
	word = Column(String, primary_key=True)
	nick = Column(String)

	def __init__(self, chan, word, nick):
		self.chan = chan
		self.word = word
		self.nick = nick


database.metadata.create_all(database.engine)
badcache = defaultdict(list)


class BadwordMatcher:
	regex = None


matcher = BadwordMatcher()


@hook.on_start()
@hook.command("loadbad", permissions=["badwords"], autohelp=False)
def load_bad(db):
	"""- Should run on start of bot to load the existing words into the regex"""
	words = []
	new_cache = defaultdict(list)
	for row in db.query(badwords).all():
		new_cache[row.chan.casefold()].append(row.word)
		words.append(rows.word)

	new_regex = re.compile(r'(\s|^|[^\w\s])({0})(\s|$|[^\w\s])'.format('|'.join(words)), re.I)

	matcher.regex = new_regex

	badcache.clear()
	badcache.update(new_cache)


@hook.command("addbad", permissions=["badwords"])
def add_bad(text, nick, db):
	"""<word> <channel> - adds a bad word to the auto kick list must specify a channel with each word"""
	splt = text.lower().split(None, 1)
	word, chan = splt
	if not chan.startswith('#'):
		return "Please specify a valid channel name after the bad word."

	word = re.escape(word)
	wordlist = list_bad(chan)
	if word in wordlist:
		return f"{word} is already added to the bad word list for {chan}"

	if len(badcache[channel]) >= 10:
		return f"There are too many words listed for channel {chan}. Please remove a word using .rmbad before adding " \
			   "anymore. For a list of bad words use .listbad"

	badword = badwords(word, nick, chan)
	db.add(badword)
	db.commit()
	load_bad(db)
	wordlist = list_bad(channel)
	return f"Current badwords: {wordlist}"


@hook.command("rmbad", "delbad", permissions=["badwords"])
def del_bad(text, db):
	"""<word> <channel> - removes the specified word from the specified channels bad word list"""
	splt = text.lower().split(None, 1)
	word, chan = splt
	if not chan.startswith('#'):
		return "Please specify a valid channel name after the bad word."

	badword = db.query(badwords) \
		.filter(badwords.word == word) \
		.filter(badwords.chan == chan) \
		.first()

	if badword:
		db.delete(badword)
		db.commit()

	newlist = list_bad(chan)
	load_bad(db)
	return f"Removing {word} new bad word list for {chan} is: {newlist}"


@hook.command("listbad", permissions=["badwords"])
def list_bad(text):
	"""<channel> - Returns a list of bad words specify a channel to see words for a particular channel"""
	text = text.split(' ')[0].lower()
	if not text.startswith('#'):
		return "Please specify a valid channel name"

	return '|'.join(badcache[text])


@hook.event([EventType.message, EventType.action], singlethread=True)
def check_badwords(conn, message, chan, content, nick):
	match = matcher.regex.match(content)
	if not match:
		return

	# Check to see if the match is for this channel
	word = match.group().lower().strip()
	if word in badcache[chan]:
		conn.cmd("KICK", chan, nick, "that fucking word is so damn offensive")
		message("{}, congratulations you've won!".format(nick))
