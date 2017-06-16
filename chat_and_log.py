from Db import *

def chat_and_log(c, target, message):
    add_log_message(target,
            c.get_nickname(),
            "pubmsg",
            message)
    c.privmsg(target, message)
