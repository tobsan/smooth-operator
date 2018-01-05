#!/usr/bin/env python3
# coding: utf-8

"""
   LogBot

   A minimal IRC log bot

   Written by Chris Oliver

   Includes python-irclib from http://python-irclib.sourceforge.net/

   This program is free software; you can redistribute it and/or
   modify it under the terms of the GNU General Public License
   as published by the Free Software Foundation; either version 2
   of the License, or any later version.

   This program is distributed in the hope that it will be useful,
   but WITHOUT ANY WARRANTY; without even the implied warranty of
   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
   GNU General Public License for more details.

   You should have received a copy of the GNU General Public License
   along with this program; if not, write to the Free Software
   Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA   02111-1307, USA.
"""


__author__ = "Chris Oliver <excid3@gmail.com>"
__version__ = "0.4.2"
__date__ = "08/11/2009"
__copyright__ = "Copyright (c) Chris Oliver"
__license__ = "GPL2"


import cgi
import os
import ftplib
import sys
import itertools
from time import strftime
try:
    from datetime import datetime
    from pytz import timezone
except: pass

try:
    from hashlib import md5
except:
    import md5

from ircbot import SingleServerIRCBot
from irclib import nm_to_n
import time
from threading import Timer

import re
from pullrequest import PullRequest
from Db import *
from flask import *
import threading
from commands import Commands
from chat_and_log import *

pat1 = re.compile(r"(^|[\n ])(([\w]+?://[\w\#$%&~.\-;:=,?@\[\]+]*)(/[\w\#$%&~/.\-;:=,?@\[\]+]*)?)", re.IGNORECASE | re.DOTALL)

#urlfinder = re.compile("(?i)\b((?:[a-z][\w-]+:(?:/{1,3}|[a-z0-9%])|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'\".,<>?«»“”‘’]))")

# We use a blueprint so that we can have a prefix in the URL
flaskapp = Blueprint('logbot-blueprint', __name__)

app = Flask(__name__)
app.config["TEMPLATES_AUTO_RELOAD"] = True

# The IP address we bind the web server to
LISTEN_IP = os.getenv("LISTEN_IP", "0.0.0.0")

# The URL prefix on the server
APPLICATION_ROOT = os.getenv("APPLICATION_ROOT", "/irclogs")
app.config["APPLICATION_ROOT"] = APPLICATION_ROOT

@app.template_filter('md5')
def format_md5(value):
    return md5(value.encode("utf-8")).hexdigest()

def urlify2(value):
    return pat1.sub(r'\1<a href="\2" target="_blank">\3</a>', value)
    #return urlfinder.sub(r'<a href="\1">\1</a>', value)

### Configuration options
DEBUG = False

# IRC Server Configuration
SERVER = os.getenv("IRC_SERVER", "irc.freenode.net")
PORT = int(os.getenv("IRC_PORT", 6667))
SERVER_PASS = os.getenv("IRC_SERVER_PASS", None)
CHANNELS = os.getenv("IRC_CHANNELS", "#pelux").split(",")
NICK = os.getenv("IRC_NICK", "pelux")
NICK_PASS = os.getenv("IRC_NICK_PASS", "")

# The local folder to save logs
LOG_FOLDER = "/var/www/html/"

# The message returned when someone messages the bot
HELP_MESSAGE = "Check out http://pelux.io!"

# FTP Configuration
FTP_SERVER = ""
FTP_USER = ""
FTP_PASS = ""
# This folder and sub folders for any channels MUST be created on the server
FTP_FOLDER = ""
# The amount of messages to wait before uploading to the FTP server
FTP_WAIT = 25

DEFAULT_TIMEZONE = 'UTC'

### Web interface

@flaskapp.route("/search/nickname/<nickname>/")
@flaskapp.route("/search/channel/<channel>/")
@flaskapp.route("/search/")
def search(channel = None, nickname = None):
    messages = []
    query = request.args.get('query')
    if channel:
        try:
            channel = Channel.get(Channel.name == channel)
            messages = LogMessage.select()                                  \
                                 .where(LogMessage.channel == channel,      \
                                        LogMessage.message.contains(query))
        except:
            pass # No such channel
    elif nickname:
        messages = LogMessage.select()                                  \
                             .where(LogMessage.nickname == nickname,    \
                                    LogMessage.message.contains(query))
    else:
        messages = LogMessage.select()                                  \
                             .where(LogMessage.message.contains(query))

    return render_template("messages.html",
            url_prefix=app.config['APPLICATION_ROOT'],
            messages=messages,
            back_button=False,
            date=True,
            channel=channel)

@flaskapp.route("/channels/<channel>/")
@flaskapp.route("/channels/<channel>/<day>/")
def channel(channel, day = None):
    channel = Channel.get(Channel.name == channel)

    if day:
        d = Day.get(Day.date == day)
        messages = LogMessage.select()                              \
                             .where(LogMessage.day == d,            \
                                    LogMessage.channel == channel)

        return render_template("messages.html",
                url_prefix=app.config['APPLICATION_ROOT'],
                messages=messages,
                back_button=True,
                date=False,
                channel=channel)
    else:
        days = LogMessage.select(LogMessage.day).distinct()
        days = [ day.day for day in days ]
        return render_template("days.html",
                url_prefix=app.config['APPLICATION_ROOT'],
                back_button=True,
                days=days,
                channel=channel)

@flaskapp.route("/")
@flaskapp.route("/channels/")
def channels():
    return render_template("channels.html",
            url_prefix=app.config['APPLICATION_ROOT'],
            back_button=True,
            channels = Channel.select())


### Helper functions

def append_line(filename, line):
    data = open(filename, "rb").readlines()[:-2]
    data += [line.encode(), "\n".encode(), "\n</body>".encode(), "\n</html>".encode()]
    write_lines(filename, data)

def write_lines(filename, lines):
    with open(filename, "wb") as f:
        f.writelines(lines)


def write_string(filename, string):
    with open(filename, "wb") as f:
        f.write(string.encode())

color_pattern = re.compile(r'(\[\d{1,2}m)')
"Pattern that matches ANSI color codes and the text that follows"

def pairs(items):
    """
    Return pairs from items

    >>> list(pairs([1,2,3,4]))
    [(1, 2), (3, 4)]
    """
    items = iter(items)
    while True:
        yield next(items), next(items)

### Logbot class

class Logbot(SingleServerIRCBot):
    def __init__(self, server, port, server_pass=None, channels=[],
                 nick="pelux", nick_pass=None):
        SingleServerIRCBot.__init__(self,
                                    [(server, port, server_pass)],
                                    nick,
                                    nick)

        self.chans = [x.lower() for x in channels]
        self.set_ftp()
        self.nick_pass = nick_pass
        self.commands = Commands()

        print("Logbot %s" % __version__)
        print("Connecting to %s:%i..." % (server, port))
        print("Press Ctrl-C to quit")

    def quit(self):
        self.connection.disconnect("Quitting...")

    def color(self, user):
        return "#%s" % md5(user.encode()).hexdigest()[:6]

    def set_ftp(self, ftp=None):
        self.ftp = ftp

    def write_event(self, event_name, event, params={}):
        target = event.target()

        if event_name == "nick":
            message = params["new"]
            target = params["chan"]
        elif event_name == "kick":
            message = "%s kicked %s from %s. Reason: %s" % (nm_to_n(params["kicker"]),
                    params["user"], params["channel"], params["reason"])
        elif event_name == "mode":
            message = "%s changed mode on %s: %s" % (params["giver"],
                    params["person"], params["modes"])
        elif event_name == "quit":
            target = params["chan"]
            message = "%s has quit" % nm_to_n(event.source())
        elif len(event.arguments()) > 0:
            message = event.arguments()[0]
        else:
            message = ""


        add_log_message(target,
                nm_to_n(event.source()),
                event_name,
                message)

    def check_for_prs(self, c):
        p = PullRequest()
        for line in p.check_all():
            message = line["message"]
            channel = line["channel"]
            chat_and_log(c, channel, message)
            time.sleep(1)

        Timer(60*5, self.check_for_prs, [c]).start()

    ### These are the IRC events

    def on_all_raw_messages(self, c, e):
        """Display all IRC connections in terminal"""
        if DEBUG: print(e.arguments()[0])

    def on_welcome(self, c, e):
        """Join channels after successful connection"""
        if self.nick_pass:
          c.privmsg("nickserv", "identify %s" % self.nick_pass)

        for chan in self.chans:
            c.join(chan)

        self.check_for_prs(c)


    def on_nicknameinuse(self, c, e):
        """Nickname in use"""
        c.nick(c.get_nickname() + "_")

    def on_invite(self, c, e):
        """Arbitrarily join any channel invited to"""
        c.join(e.arguments()[0])
        #TODO: Save? Rewrite config file?

    ### Loggable events

    def on_action(self, c, e):
        """Someone says /me"""
        self.write_event("action", e)

    def on_join(self, c, e):
        self.write_event("join", e)

    def on_kick(self, c, e):
        self.write_event("kick", e,
                         {"kicker" : e.source(),
                          "channel" : e.target(),
                          "user" : e.arguments()[0],
                          "reason" : e.arguments()[1],
                         })

    def on_mode(self, c, e):
        self.write_event("mode", e,
                         {"modes" : e.arguments()[0],
                          "person" : e.arguments()[1] if len(e.arguments()) > 1 else e.target(),
                          "giver" : nm_to_n(e.source()),
                         })

    def on_nick(self, c, e):
        old_nick = nm_to_n(e.source())
        # Only write the event on channels that actually had the user in the channel
        for chan in self.channels:
            if old_nick in [x.lstrip('~%&@+') for x in self.channels[chan].users()]:
                self.write_event("nick", e,
                             {"old" : old_nick,
                              "new" : e.target(),
                              "chan": chan,
                             })

    def on_part(self, c, e):
        self.write_event("part", e)

    def on_pubmsg(self, c, e):
#        if e.arguments()[0].startswith(NICK):
#            c.privmsg(e.target(), self.format["help"])
        self.write_event("pubmsg", e)
        self.commands.process(c, e)

    def on_pubnotice(self, c, e):
        self.write_event("pubnotice", e)

    def on_privmsg(self, c, e):
#        c.privmsg(nm_to_n(e.source()), self.format["help"])
        self.commands.process(c, e)
        pass

    def on_quit(self, c, e):
        nick = nm_to_n(e.source())
        # Only write the event on channels that actually had the user in the channel
        for chan in self.channels:
            if nick in [x.lstrip('~%&@+') for x in self.channels[chan].users()]:
                self.write_event("quit", e, {"chan" : chan})

    def on_topic(self, c, e):
        self.write_event("topic", e)

def connect_ftp():
    print("Using FTP %s..." % (FTP_SERVER))
    f = ftplib.FTP(FTP_SERVER, FTP_USER, FTP_PASS)
    f.cwd(FTP_FOLDER)
    return f

def main():
    # Start up database
    create_tables()

    # Register the blueprint. This is a bit of a hack
    app.register_blueprint(flaskapp, url_prefix=app.config['APPLICATION_ROOT'])

    t = threading.Thread(target=app.run, kwargs={"host": LISTEN_IP})
    t.daemon = True
    t.start()

    # Create the logs directory
    if not os.path.exists(LOG_FOLDER):
        os.makedirs(LOG_FOLDER)
        write_string("%s/index.html" % LOG_FOLDER, html_header.replace("%title%", "Chat Logs"))

    # Start the bot
    bot = Logbot(SERVER, PORT, SERVER_PASS, CHANNELS, NICK, NICK_PASS)
    try:
        # Connect to FTP
        if FTP_SERVER:
            bot.set_ftp(connect_ftp())

        bot.start()
    except KeyboardInterrupt:
        if FTP_SERVER: bot.ftp.quit()
        bot.quit()


if __name__ == "__main__":
    main()
