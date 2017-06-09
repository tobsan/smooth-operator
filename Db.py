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


def create_tables():
    database.connect()
    try:
        database.create_tables([LogMessage, Day, Channel])
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
            datetime = datetime.datetime.now().strftime("%H:%m:%S"),
            message_type = message_type,
            message = message)

def show_all_messages():
    for message in LogMessage.select():
        print("<%s> %s" % (message.nickname, message.message))
