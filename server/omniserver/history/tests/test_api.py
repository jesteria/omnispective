import json

from django.contrib.auth import models as auth
from django.core.urlresolvers import reverse
from tastypie.test import ResourceTestCase

from history import models as history


class ApiTestCase(ResourceTestCase):

    def setUp(self):
        super(ApiTestCase, self).setUp()
        self.user = auth.User.objects.create(username='client')
        self.apikey_credentials = self.create_apikey(self.user.username,
                                                     self.user.api_key.key)
        self.app = history.App.objects.create(code='myapp', name='My App')


class TestAppApi(ApiTestCase):

    def test_get_list_json(self):
        response = self.api_client.get(
            reverse('api_dispatch_list', kwargs={'resource_name': 'app'}),
            format='json',
            authentication=self.apikey_credentials,
        )
        self.assertValidJSONResponse(response)
        data = json.loads(response.content)
        self.assertEqual(data['meta']['total_count'], 1)

    def test_get_detail_json(self):
        response = self.api_client.get(
            reverse('api_dispatch_detail', kwargs={'resource_name': 'app',
                                                   'code': self.app.code}),
            format='json',
            authentication=self.apikey_credentials,
        )
        self.assertValidJSONResponse(response)
        data = json.loads(response.content)
        self.assertEqual(data['name'], self.app.name)


class TestClientRequestApi(ApiTestCase):

    def setUp(self):
        super(TestClientRequestApi, self).setUp()
        self.base_url = reverse('api_dispatch_list',
                                kwargs={'resource_name': 'clientrequest'})
        self.can_add_request = auth.Permission.objects.get(
            content_type__app_label='history',
            codename='add_clientrequest',
        )
        self.can_add_session = auth.Permission.objects.get(
            content_type__app_label='history',
            codename='add_clientsession',
        )
        self.user.user_permissions.add(self.can_add_request)
        self.user.user_permissions.add(self.can_add_session)

    def test_get_list_json_unauthorized(self):
        response = self.api_client.get(self.base_url, format='json')
        self.assertHttpUnauthorized(response)

    def test_get_list_json(self):
        response = self.api_client.get(
            self.base_url,
            format='json',
            authentication=self.apikey_credentials,
        )
        self.assertValidJSONResponse(response)
        self.assertContains(response, '{"meta": {"limit')

    def test_post_request_json_unauthorized(self):
        client_requests = history.ClientRequest.objects.all()
        count0 = client_requests.count()
        response = self.api_client.post(
            self.base_url,
            format='json',
            data={
                'method': 'teapot',
                'protocol': 'https:',
                'host': 'example.com',
                'path': '/mypath/',
                'full_path': 'https://example.com/mypath/?key=value',
                'remote_addr': '0.0.0.0',
                'session': {
                    'key': '01234ABCD',
                    'app': self.app.code,
                },
            },
        )
        self.assertHttpUnauthorized(response)
        self.assertEqual(client_requests.count(), count0)

    def test_post_request_json_unauthorized_nouser(self):
        client_requests = history.ClientRequest.objects.all()
        count0 = client_requests.count()
        self.user.delete()
        response = self.api_client.post(
            self.base_url,
            format='json',
            data={
                'method': 'teapot',
                'protocol': 'https:',
                'host': 'example.com',
                'path': '/mypath/',
                'full_path': 'https://example.com/mypath/?key=value',
                'remote_addr': '0.0.0.0',
                'session': {
                    'key': '01234ABCD',
                    'app': self.app.code,
                },
            },
            authentication=self.apikey_credentials,
        )
        self.assertHttpUnauthorized(response)
        self.assertEqual(client_requests.count(), count0)

    def test_post_request_json_unauthorized_noperm(self):
        client_requests = history.ClientRequest.objects.all()
        client_sessions = history.ClientSession.objects.all()
        request_count0 = client_requests.count()
        session_count0 = client_sessions.count()
        self.user.user_permissions.remove(self.can_add_request)
        response = self.api_client.post(
            self.base_url,
            format='json',
            data={
                'method': 'teapot',
                'protocol': 'https:',
                'host': 'example.com',
                'path': '/mypath/',
                'full_path': 'https://example.com/mypath/?key=value',
                'remote_addr': '0.0.0.0',
                'session': {
                    'key': '01234ABCD',
                    'app': self.app.code,
                },
            },
            authentication=self.apikey_credentials,
        )
        self.assertHttpUnauthorized(response)
        self.assertEqual(client_requests.count(), request_count0)
        self.assertEqual(client_sessions.count(), session_count0)

    def test_post_request_json(self):
        client_requests = history.ClientRequest.objects.all()
        count0 = client_requests.count()
        response = self.api_client.post(
            self.base_url,
            format='json',
            data={
                'method': 'teapot',
                'protocol': 'https:',
                'host': 'example.com',
                'path': '/mypath/',
                'full_path': 'https://example.com/mypath/?key=value',
                'remote_addr': '0.0.0.0',
                'session': {
                    'key': '01234ABCD',
                    'app': self.app.code,
                },
            },
            authentication=self.apikey_credentials,
        )
        self.assertHttpCreated(response)
        self.assertEqual(client_requests.count(), count0 + 1)

        client_request = client_requests.latest()
        self.assertEqual(client_request.method, 'teapot')
        self.assertEqual(client_request.get_protocol_display(), 'HTTPS')
        self.assertEqual(client_request.host, 'example.com')
        self.assertEqual(client_request.path, '/mypath/')
        self.assertEqual(client_request.full_path,
                         'https://example.com/mypath/?key=value')
        self.assertEqual(client_request.remote_addr, '0.0.0.0')
        self.assertEqual(client_request.session.key, '01234ABCD')
        self.assertEqual(client_request.session.app, self.app)
