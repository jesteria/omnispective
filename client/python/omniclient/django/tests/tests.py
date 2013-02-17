import mock
from django.test import RequestFactory
from django.test.utils import override_settings
from unittest import TestCase

from omniclient.django.middleware import OmnispectiveMiddleware


class TestBasicMiddleware(TestCase):

    def setUp(self):
        self.mw = OmnispectiveMiddleware()
        self.factory = RequestFactory()

    @override_settings(
        OMNISPECTIVE_HOST='example.com',
        OMNISPECTIVE_USERNAME='client',
        OMNISPECTIVE_API_KEY='1234',
    )
    @mock.patch('omniclient.django.base.requests')
    def test_store_interaction(self, requests):
        request = self.factory.get('/hello/')
        self.assertRaises( # FIXME
            NotImplementedError, self.mw.process_response, request, None)
        posts = requests.post.call_args_list
        self.assertEqual(len(posts), 1) # FIXME: for now
        request_post = posts[0]
        self.assertEqual(request_post[0],
            ('https://example.com/api/clientrequest/?format=json',))
        self.assertEqual(request_post[1], {
            'headers': {
                'content-type': 'application/json',
                'authorization': 'ApiKey client:1234',
            },
            'data': '{}' # FIXME: for now
        })
