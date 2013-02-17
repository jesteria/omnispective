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


def _install(where, requirements, checkouts=()):
    reqs = ' '.join('-r {0}'.format(file_) for file_ in requirements)
    cos = ' '.join('-e {0}'.format(co) for co in checkouts)
    with fab.lcd(ROOT):
        fab.local('pip install -E {where}{reqs}{cos}'.format(
            where=where,
            reqs=(reqs and ' ' + reqs),
            cos=(cos and ' ' + cos),
        ))


def _build_server():
    env_dir = _make_virtualenv('server.env')
    test_requirements = os.path.join('server', 'test.requirements')
    _install(env_dir, [test_requirements], ['server'])


def _build_client():
    env_dir = _make_virtualenv('client.env')
    test_requirements = os.path.join('client', 'python', 'test.requirements')
    checkout = os.path.join('client', 'python')
    _install(env_dir, [test_requirements], [checkout])


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
