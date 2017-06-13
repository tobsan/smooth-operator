# smooth-operator

smooth-operator is a IRC bot which logs everything in a channel and offers more convinient things like notifications about new commits on GitHub, etc. For a roadmap please check the issues on GitHub.

Originally this was written by Chris Oliver <chris@excid3.com> with contributions from Filip Slagter. Now it has diverged quite a lot.

## Requirements

smooth-operator shows logs using flask, and stores logs using peewee. Install these dependencies using ``pip``:

    pip install flask peewee requests

## Usage

smooth-operator requires Python 2. It is NOT compatible with Python 3. Configuration is either done inside logbot.py, or using environment variables. The following environment variables are respected:

- ``IRC_SERVER``: IRC server
- ``IRC_PORT``: IRC server port
- ``IRC_SERVER_PASS``: Password for IRC server, if any
- ``IRC_CHANNELS``: IRC channels to join, separated by ``,``
- ``IRC_NICK``: Nickname
- ``IRC_NICK_PASS``: Password to use when authenticating to nickserv, if any

The bot can be launched using:

    python2 logbot.py

You can view the logs on http://localhost:5000

## License

This project is licensed under the GPLv2.
