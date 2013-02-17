import os.path
import textwrap

from fabric import api as fab


ROOT = os.path.dirname(os.path.abspath(__file__))


def _make_virtualenv(name, hidden=True):
    prefix = '.' if hidden else ''
    dir_ = os.path.join(ROOT, prefix + name)
    fab.local('virtualenv {0} --prompt="({1})"'.format(dir_, name))
    fab.puts(textwrap.dedent('''
        Activate virtual environment {0} with:
            source {1}/bin/activate
        '''.format(name, dir_)))
    return dir_


def _build_server():
    dir_ = _make_virtualenv('server.env')
    with fab.lcd(ROOT):
        fab.local('pip install -E {0} -e server'.format(dir_))


def _build_client():
    dir_ = _make_virtualenv('client.env')
    with fab.lcd(ROOT):
        fab.local('pip install -E {0} -e client/python'.format(dir_))


def build(what):
    """Build a package for local development.

        build:server
        build:client

    """
    try:
        func = globals()["_build_%s" % what]
    except KeyError:
        pass
    else:
        if callable(func):
            func()
            return

    fab.abort("No such build target {0!r}".format(what))
