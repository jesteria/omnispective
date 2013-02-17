from omniclient import ConfigurationError

from .base import OmnispectiveClient


class NoCeleryTask(object):

    def __call__(self, _task):
        return self

    def __getattribute__(self, _key):
        raise ConfigurationError("Missing dependency 'celery'")


try:
    from celery import task
except ImportError:
    task = NoCeleryTask


@task()
def process_request(data):
    OmnispectiveClient.post_request(data)

@task()
def process_response(data):
    OmnispectiveClient.post_response(data)
