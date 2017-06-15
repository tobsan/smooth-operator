from Db import *
from irclib import nm_to_n
import random

class Commands:
    def __init__(self):
        self.commands = {
            "quote": self.cmd_quote,
            "remember_quote": self.cmd_remember_quote
        }

    def process(self, c, e):
        msg = e.arguments()[0]
        if msg.startswith("!"):
            cmd = msg.split("!")[1].split(" ")[0]
            if cmd in self.commands:
                msg = " ".join(msg.split(" ")[1:])
                self.commands[cmd](c, msg, e.target(), nm_to_n(e.source()))
            else:
                print ("Unknown command", cmd)

    def cmd_quote(self, c, msg, target, source):
        replies = [
            "%s once said \"%s\"",
            "I head from %s that \"%s\"",
            "A wise man (haha, just kidding, it was actually %s) once said \"%s\""
        ]
        reply = lambda msg: c.privmsg(target, msg)
        random_query = Quote.select().order_by(fn.Random())
        try:
            one_quote = random_query.get()
            reply(random.choice(replies) % (one_quote.author, one_quote.message))
        except: # No quotes
            reply("I don't know ay quotes :(")

    def cmd_remember_quote(self, c, msg, target, source):
        reply = lambda msg: c.privmsg(target, msg)

        if (len(msg) > 1):
            add_quote(msg.split(" ")[0], ' '.join(msg.split(" ")[1:]))
            reply("I'll try to remember that!")
        else:
            reply("I didn't get that :(")

