from peewee import *
import datetime

DATABASE = "irc.db"

database = SqliteDatabase(DATABASE)

class BaseModel(Model):
    class Meta:
        database = database

class Day(BaseModel):
    date = CharField()

class Channel(BaseModel):
    name = CharField(unique = True)

class LogMessage(BaseModel):
    day = ForeignKeyField(Day)
    channel = ForeignKeyField(Channel)
    nickname = CharField()
    datetime = DateTimeField()
    message_type = CharField()
    message = CharField()

class Quote(BaseModel):
    datetime = DateTimeField()
    author = CharField()
    message = CharField()

class Teller(BaseModel):
    datetime = DateTimeField()
    author = CharField()
    location = CharField()
    recipient = CharField()
    message = CharField()

def create_tables():
    database.connect()
    try:
        database.create_tables([Teller, Quote, LogMessage, Day, Channel])
    except OperationalError:
        pass # Database already exists

def get_current_day():
    today = datetime.date.today()
    try:
        return Day.get(Day.date == today)
    except:
        Day.create(date = today)
        return Day.get(Day.date == today)

def get_channel(c):
    try:
        return Channel.get(Channel.name == c)
    except:
        Channel.create(name = c)
        return Channel.get(Channel.name == c)

def add_log_message(channel, nickname, message_type, message = None):
    msg = LogMessage.create(
            day = get_current_day(),
            channel = get_channel(channel),
            nickname = nickname,
            datetime = datetime.datetime.now().strftime("%H:%M:%S"),
            message_type = message_type,
            message = message)

def add_quote(author, message):
    Quote.create(
            author = author,
            message = message,
            datetime = datetime.datetime.now().strftime("%H:%M:%S"))

def add_tell_message(author, location, recipient, message):
    Teller.create(
            author = author,
            location = location,
            recipient = recipient,
            message = message,
            datetime = datetime.datetime.now().strftime("%H:%M:%S"))

def get_told_messages(recipient):
    try:
        return Teller.select().where(Teller.recipient == recipient);
    except:
        return []

def remove_told_messages(recipient):
    q = Teller.delete().where(Teller.recipient == recipient)
    q.execute()

def show_all_messages():
    for message in LogMessage.select():
        print("<%s> %s" % (message.nickname, message.message))
