import requests

from . import settings


class OmnispectiveClient(object):

    @staticmethod
    def get_url(resource):
        if settings.HOST_IS_SECURE:
            protocol = 'https:'
        else:
            protocol = 'http:'
        return '{protocol}//{host}/api/{resource}/?format=json'.format(
            protocol=protocol,
            host=settings.HOST,
            resource=resource,
        )

    @staticmethod
    def get_headers():
        auth = 'ApiKey {0}:{1}'.format(settings.USERNAME, settings.API_KEY)
        return {
            'authorization': auth,
            'content-type': 'application/json',
        }

    @classmethod
    def post_request(cls, data):
        requests.post(
            cls.get_url('clientrequest'),
            headers=cls.get_headers(),
            data=data,
        )

    @classmethod
    def post_response(cls, data):
        raise NotImplementedError
