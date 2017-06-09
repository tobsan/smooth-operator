# smooth-operator

smooth-operator is a IRC bot which logs everything in a channel and offers more convinient things like notifications about new commits on GitHub, etc. For a roadmap please check the issues on GitHub.

Originally this was written by Chris Oliver <chris@excid3.com> with contributions from Filip Slagter. Now it has diverged quite a lot.

## Requirements

smooth-operator shows logs using flask, and stores logs using peewee. Install these dependencies using ``pip``:

    pip install flask peewee

## Usage

smooth-operator requires Python 2. It is NOT compatible with Python 3. The Configuration is done inside logbot.py.

    python2 logbot.py

You can view the logs on http://localhost:5000

## License

This project is licensed under the GPLv2.
