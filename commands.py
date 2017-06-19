from Db import *
from irclib import nm_to_n, is_channel
import random
from chat_and_log import *

class Commands:


    def __init__(self):
        self.commands = {
            "quote": self.cmd_quote,
            "remember_quote": self.cmd_remember_quote,
            "tell": self.cmd_tell,
            "messages": self.cmd_get_tell_messages
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

    def create_reply(self, c, target, source):
        reply_target = target if is_channel(target) else source
        reply = lambda msg: chat_and_log(c, reply_target, msg)
        return reply

    def cmd_quote(self, c, msg, target, source):
        replies = [
            "%s once said \"%s\"",
            "I head from %s that \"%s\"",
            "A wise man (haha, just kidding, it was actually %s) once said \"%s\""
        ]
        reply = self.create_reply(c, target, source)
        random_query = Quote.select().order_by(fn.Random())
        try:
            one_quote = random_query.get()
            reply(random.choice(replies) % (one_quote.author, one_quote.message))
        except: # No quotes
            reply("I don't know ay quotes :(")

    def cmd_remember_quote(self, c, msg, target, source):
        reply = self.create_reply(c, target, source)

        if (len(msg) > 1):
            add_quote(msg.split(" ")[0], ' '.join(msg.split(" ")[1:]))
            reply("I'll try to remember that!")
        else:
            reply("I didn't get that :(")

    def cmd_tell(self, c, msg, target, source):
        reply = self.create_reply(c, target, source)

        msgparts = msg.split(" ")
        recipient = msgparts[0]
        message = " ".join(msgparts[1:])
        location = target if is_channel(target) else "private"

        add_tell_message(source, location, recipient, message)
        reply("I'll save that message for %s" % recipient)

    def cmd_get_tell_messages(self, c, msg, target, source):
        reply = self.create_reply(c, target, source)
        messages = get_told_messages(source)
        if not messages:
            reply("There are no messages")
        else:
            for message in messages:
                reply("%s said (at %s, in %s): %s" % (message.author, message.datetime, message.location, message.message))
            remove_told_messages(source)
