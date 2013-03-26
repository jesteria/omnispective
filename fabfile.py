import functools
import os.path
import textwrap

from fabric import api as fab


ROOT = os.path.dirname(os.path.abspath(__file__))

PROJECTS = 'client', 'server'
_NICE_PROJECTS = map(repr, PROJECTS)
PROJECT_ERROR = "Select {0}".format(' or '.join([', '.join(_NICE_PROJECTS[:-1]),
                                                _NICE_PROJECTS[-1]]))


# Decorators #

def keyword_options(*exclude, **kws):
    """Provide the decorated function with additional keyword arguments based
    on its (unexcluded) keyword arguments, for use on the command line.

        boolean: whether to treat anonymous arguments as boolean flags

    Adds to the keyword dictionary of the decorated function the following:

        arguments: a space-delimited string of anonymous arguments
        arguments_nice: the same as arguments, but with a leading space,
            if arguments is non-empty
        options: a space-delimited string of keyword arguments, converted
            into --KEY=VALUE format. Includes anonymous arguments in --FLAG
            format when boolean is True.

    """
    boolean = kws.pop('boolean', False)
    if kws:
        raise TypeError("Unexpected keyword argument(s): %s" % ', '.join(kws))

    def decorator(func):
        @functools.wraps(func)
        def task(*args, **kws):
            options = ' '.join('--{key}={value}'.format(key=key, value=value)
                                 for key, value in kws.items()
                                 if key not in exclude)
            if boolean:
                flags = ' '.join('--{0}'.format(flag) for flag in args)
                options = ' '.join(part for part in (flags, options) if part)
                arguments = ''
            else:
                arguments = ' '.join(args)
            return func(*args,
                        arguments=arguments,
                        arguments_nice=(arguments and ' {0}'.format(arguments)),
                        options=options,
                        options_nice=(options and ' {0}'.format(options)),
                        **kws)
        return task

    if len(exclude) == 1 and callable(exclude[0]):
        return decorator(exclude[0])
    return decorator


def require_project(func):
    @functools.wraps(func)
    def task(*args, **kws):
        try:
            what = fab.env.project
        except AttributeError:
            fab.abort("No project specified. {0}.".format(PROJECT_ERROR))
        else:
            kws.setdefault('project', what)
            return func(*args, **kws)
    return task


# Helpers #

def make_virtualenv(name, hidden=True):
    """Create a virtualenv with the given name.

    According to ``hidden``, and by default, the virtualenv will be created
    in a *nix-hidden directory (its name preceded by a single dot).

    """
    prefix = '.' if hidden else ''
    dir_ = os.path.join(ROOT, prefix + name)
    fab.local('virtualenv {0} --prompt="({1})"'.format(dir_, name))
    fab.puts(textwrap.dedent('''
        Activate virtual environment {0} with:
            source {1}/bin/activate
        '''.format(name, dir_)))
    return dir_


def install(requirements, checkouts=(), where=''):
    """Install the specified code checkouts and requirements files.

    Optionally pass to pip the path of the virtualenv into which to install
    (-E) with ``where`` (deprecated).

    """
    reqs = ' '.join('-r {0}'.format(file_) for file_ in requirements)
    cos = ' '.join('-e {0}'.format(co) for co in checkouts)
    with fab.lcd(ROOT):
        fab.local('pip install {where}{reqs}{cos}'.format(
            where=(where and '-E ' + where),
            reqs=(reqs and ' ' + reqs),
            cos=(cos and ' ' + cos),
        ))


# Proxied task functions #

def build_server():
    """Build the server environment."""
    make_virtualenv('server.env')
    test_requirements = os.path.join('server', 'test.requirements')
    install([test_requirements], ['server'])


def build_client():
    """Build the client environment."""
    make_virtualenv('client.env')
    test_requirements = os.path.join('client', 'python', 'test.requirements')
    checkout = os.path.join('client', 'python')
    install([test_requirements], [checkout])


@keyword_options
def test_server(*apps, **kws):
    """Run unit tests locally for a given application, or by default for all
    server applications.

        test:history,verbosity=2

    """
    apps = apps or ['history']
    with fab.lcd(os.path.join(ROOT, 'server/omniserver/')):
        fab.local('python manage.py test {apps}{extra}'.format(
            apps=' '.join(apps),
            extra=kws['options_nice'],
        ))


@keyword_options(boolean=True)
def test_client(*args, **kws):
    """Run unit tests locally for the client package.

        test:pdb-fail,verbosity=2

    """
    with fab.lcd(os.path.join(ROOT, 'client/python/')):
        fab.local('python omniclient/django/tests/run.py test{options}'.format(
            options=kws['options_nice'],
        ))


def set_project(name):
    """Set the given project namespace.

    Stores the project in the Fabric env to direct following tasks, and sets
    the virtualenv PATH.

    """
    if name not in PROJECTS:
        fab.abort("No such project '{0}'. {1}.".format(name, PROJECT_ERROR))
    fab.env.project = name
    env_path = '.{0}.env/bin'.format(name)
    fab.env.command_prefixes.append(
        "PATH={0}:$PATH".format(os.path.join(ROOT, env_path))
    )


# Tasks #

@fab.task
def client():
    """Set the "client" project namespace

    Required by many tasks. E.g.:

        client test

    """
    set_project('client')


@fab.task
def server():
    """Set the "server" project namespace

    Required by many tasks. E.g.:

        server test

    """
    set_project('server')


@fab.task
@require_project
def build(project):
    """Build a project for local development

        server build
        client build

    """
    try:
        func = globals()["build_%s" % project]
    except KeyError:
        pass
    else:
        if callable(func):
            func()
            return

    fab.abort("No such build target {0!r}".format(project))


@fab.task
@require_project
def test(*args, **kws):
    """Execute a project's tests

        server test
        client test:verbosity=2

    """
    what = kws.pop('project')

    try:
        func = globals()['test_{0}'.format(what)]
    except KeyError:
        pass
    else:
        if callable(func):
            func(*args, **kws)
            return

    fab.abort("No such test target {0!r}".format(what))
