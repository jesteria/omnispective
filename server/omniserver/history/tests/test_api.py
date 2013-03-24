import json
import textwrap

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
        ''' Test asserting that we can receive a list of history.App
        resources from the API
        '''
        response = self.api_client.get(
            reverse('api_dispatch_list', kwargs={'resource_name': 'app'}),
            format='json',
            authentication=self.apikey_credentials,
        )
        self.assertValidJSONResponse(response)
        data = json.loads(response.content)
        self.assertEqual(data['meta']['total_count'], 1)

    def test_get_detail_json(self):
        ''' Test asserting that we can receive a history.App object via the
        API
        '''
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
        self.get_mypath = textwrap.dedent('''\
            GET /mypath/?key=value HTTP/1.0
            User-Agent: Test/0.1
            ''')
        self.post_mypath = textwrap.dedent('''\
            POST /mypath/?get=query HTTP/1.0
            User-Agent: Test/0.1
            Other-Header: This

            the=pay-load&such=%26such
            ''')
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
        ''' Test asserting that we block unauthorized users from grabbing a
        list of ClientRequest objects
        '''
        response = self.api_client.get(self.base_url, format='json')
        self.assertHttpUnauthorized(response)

    def test_get_list_json(self):
        ''' Test asserting we can retrieve a list of ClientResource objects
        as an authorized user
        '''
        response = self.api_client.get(
            self.base_url,
            format='json',
            authentication=self.apikey_credentials,
        )
        self.assertValidJSONResponse(response)
        self.assertContains(response, '{"meta": {"limit')

    def test_post_request_json_unauthorized(self):
        ''' Test asserting that we block unauthorized users from posting a
        a ClientRequest
        '''
        client_requests = history.ClientRequest.objects.all()
        count0 = client_requests.count()
        response = self.api_client.post(
            self.base_url,
            format='json',
            data={
                'content': self.get_mypath,
                'full_url': 'https://example.com/mypath/?key=value',
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
        ''' Test asserting that a user must exist in order to post to the
        ClientRequest API endpoint
        '''
        client_requests = history.ClientRequest.objects.all()
        count0 = client_requests.count()
        self.user.delete()
        response = self.api_client.post(
            self.base_url,
            format='json',
            data={
                'content': self.get_mypath,
                'full_url': 'https://example.com/mypath/?key=value',
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
        ''' Test asserting that a user must have proper permissions in order
        to post to the ClientRequest API endpoint
        '''
        client_requests = history.ClientRequest.objects.all()
        client_sessions = history.ClientSession.objects.all()
        request_count0 = client_requests.count()
        session_count0 = client_sessions.count()
        self.user.user_permissions.remove(self.can_add_request)
        response = self.api_client.post(
            self.base_url,
            format='json',
            data={
                'content': self.get_mypath,
                'full_url': 'https://example.com/mypath/?key=value',
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

    def test_post_GET_request_json(self):
        ''' Testing the ability to create a new ClientRequest object via a
        post to the ClientRequest API endpoint. Tracking a GET request by a
        client, and asserting that we properly map all of the data
        '''
        client_requests = history.ClientRequest.objects.all()
        count0 = client_requests.count()
        response = self.api_client.post(
            self.base_url,
            format='json',
            data={
                'content': self.get_mypath,
                'full_url': 'https://example.com/mypath/?key=value',
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
        self.assertEqual(client_request.method, 'GET')
        self.assertEqual(client_request.get_protocol_display(), 'HTTPS')
        self.assertEqual(client_request.host, 'example.com')
        self.assertEqual(client_request.path, '/mypath/')
        self.assertEqual(client_request.query_params.urlencoded(), 'key=value')
        self.assertEqual(client_request.full_url,
                         'https://example.com/mypath/?key=value')
        self.assertEqual(client_request.user_agent, 'Test/0.1')
        self.assertEqual(client_request.remote_addr, '0.0.0.0')
        self.assertEqual(client_request.session.key, '01234ABCD')
        self.assertEqual(client_request.session.app, self.app)

    def test_post_POST_request_json(self):
        ''' Testing the ability to create a new ClientRequest object via a
        post to the ClientRequest API endpoint. Tracking a POST request by a
        client, and asserting that we properly map all of the data
        '''
        client_requests = history.ClientRequest.objects.all()
        count0 = client_requests.count()
        response = self.api_client.post(
            self.base_url,
            format='json',
            data={
                'content': self.post_mypath,
                'full_url': 'http://example.com/mypath/?get=query',
                'remote_addr': '192.0.1.2',
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
        self.assertEqual(client_request.method, 'POST')
        self.assertEqual(client_request.get_protocol_display(), 'HTTP')
        self.assertEqual(client_request.host, 'example.com')
        self.assertEqual(client_request.path, '/mypath/')
        self.assertEqual(client_request.query_params.urlencoded(), 'get=query')
        self.assertEqual(client_request.full_url,
                         'http://example.com/mypath/?get=query')
        self.assertEqual(
            list(client_request.form_params.values_list('key', 'value')),
            [('the', 'pay-load'), ('such', '&such')]
        )
        self.assertEqual(client_request.user_agent, 'Test/0.1')
        self.assertEqual(client_request.remote_addr, '192.0.1.2')
        self.assertEqual(client_request.session.key, '01234ABCD')
        self.assertEqual(client_request.session.app, self.app)

    def test_invalid_app_name(self):
        ''' Test asserting that a proper app name must be provided when
        submitting a client's request to the ClientRequest API endpoint
        '''
        response = self.api_client.post(
            self.base_url,
            format='json',
            data={
                'content': self.get_mypath,
                'full_url': 'https://example.com/mypath/?key=value',
                'remote_addr': '0.0.0.0',
                'session': {
                    'key': '01234ABCD',
                    'app': 'bogus',
                },
            },
            authentication=self.apikey_credentials,
        )
        content = json.loads(response.content)
        self.assertHttpBadRequest(response)
        self.assertEqual(content['error'], 'App code missing or invalid')
