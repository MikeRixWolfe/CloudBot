import logging

from sqlalchemy import Column, String

from cloudbot import hook
from cloudbot.util import database


class regex_chans(database.base):
	__tablename__ = 'regex_chans'
	__table_args__ = {'extend_existing': True}

	conn = Column(String, primary_key=True)
	chan = Column(String, primary_key=True)
	status = Column(String)

	def __init__(self, conn, chan, status):
		self.conn = conn
		self.chan = chan
		self.status = status

# Default value.
# If True, all channels without a setting will have regex enabled
# If False, all channels without a setting will have regex disabled
default_enabled = True
database.metadata.create_all(database.engine)
status_cache = {}
logger = logging.getLogger("cloudbot")


@hook.on_start()
def load_cache(db):
	"""
	:type db: sqlalchemy.orm.Session
	"""
	new_cache = {}
	for row in db.query(regex_chans).all():
		new_cache[(row.conn, row.chan)] = row.status

	status_cache.clear()
	status_cache.update(new_cache)


def set_status(db, conn, chan, status):
	if (conn, chan) in status_cache:
		regex_chan = db.query(regex_chans) \
			.filter(regex_chans.conn == conn) \
			.filter(regex_chans.chan == chan) \
			.first()

		regex_chan.status = status
	else:
		regex_chan = regex_chans(conn, chan, status)
		db.add(regex_chan)

	db.commit()


def delete_status(db, conn, chan):
	regex_chan = db.query(regex_chans) \
		.filter(regex_chans.conn == conn) \
		.filter(regex_chans.chan == chan) \
		.first()

	if regex_chan:
		db.delete(regex_chan)
		db.commit()


@hook.sieve()
def sieve_regex(bot, event, _hook):
	if _hook.type == "regex" and event.chan.startswith("#") and _hook.plugin.title != "factoids":
		status = status_cache.get((event.conn.name, event.chan))
		if status != "ENABLED" and (status == "DISABLED" or not default_enabled):
			logger.info("[%s] Denying %s from %s", event.conn.name, _hook.function_name, event.chan)
			return None
		logger.info("[%s] Allowing %s to %s", event.conn.name, _hook.function_name, event.chan)

	return event


def change_status(db, event, status):
	text = event.text.strip().lower()
	if not text:
		channel = event.chan
	elif text.startswith("#"):
		channel = text
	else:
		channel = "#{}".format(text)

	action = "Enabling" if status else "Disabling"
	event.message(
		"{} regex matching (youtube, etc) (issued by {})".format(action, event.nick),
		target=channel
	)
	event.notice("{} regex matching (youtube, etc) in channel {}".format(
		action, channel
	))
	set_status(db, event.conn.name, channel, "ENABLED" if status else "DISABLED")
	load_cache(db)


@hook.command(autohelp=False, permissions=["botcontrol"])
def enableregex(db, event):
	"""[chan] - Enable regex hooks in [chan] (default: current channel)"""
	return change_status(db, event, True)


@hook.command(autohelp=False, permissions=["botcontrol"])
def disableregex(db, event):
	"""[chan] - Disable regex hooks in [chan] (default: current channel)"""
	return change_status(db, event, False)


@hook.command(autohelp=False, permissions=["botcontrol"])
def resetregex(text, db, conn, chan, nick, message, notice):
	"""[chan] - Reset regex hook status in [chan] (default: current channel)"""
	text = text.strip().lower()
	if not text:
		channel = chan
	elif text.startswith("#"):
		channel = text
	else:
		channel = "#{}".format(text)

	message("Resetting regex matching setting (youtube, etc) (issued by {})".format(nick), target=channel)
	notice("Resetting regex matching setting (youtube, etc) in channel {}".format(channel))
	delete_status(db, conn.name, channel)
	load_cache(db)


@hook.command(autohelp=False, permissions=["botcontrol"])
def regexstatus(text, conn, chan):
	"""[chan] - Get status of regex hooks in [chan] (default: current channel)"""
	text = text.strip().lower()
	if not text:
		channel = chan
	elif text.startswith("#"):
		channel = text
	else:
		channel = "#{}".format(text)
	status = status_cache.get((conn.name, chan))
	if status is None:
		if default_enabled:
			status = "ENABLED"
		else:
			status = "DISABLED"
	return "Regex status for {}: {}".format(channel, status)


@hook.command(autohelp=False, permissions=["botcontrol"])
def listregex(conn):
	"""- List non-default regex statuses for channels"""
	values = []
	for (conn_name, chan), status in status_cache.values():
		if conn_name != conn.name:
			continue
		values.append("{}: {}".format(chan, status))
	return ", ".join(values)
