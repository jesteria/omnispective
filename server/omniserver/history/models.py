import httplib
import urllib
import urlparse

from django.contrib.auth.models import User
from django.db import models
from django.db.models.query import QuerySet
from tastypie.models import create_api_key

from history import util


class BaseModel(models.Model):

    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    def __str__(self):
        return unicode(self).encode('utf-8')

    class Meta(object):
        abstract = True


class App(BaseModel):

    code = models.SlugField(unique=True)
    name = models.CharField(max_length=100)

    def __unicode__(self):
        return u'{0}'.format(self.name)


class Client(BaseModel):

    app = models.ForeignKey('history.App', related_name='clients')
    username = models.CharField(max_length=200, db_index=True)

    class Meta(object):
        unique_together = ('app', 'username')

    def __unicode__(self):
        return u'{0} on {1}'.format(self.username, self.app)


class ClientSession(BaseModel):

    key = models.CharField(max_length=255, db_index=True)
    linked_sessions = models.ManyToManyField('history.ClientSession') # TODO: 16
    app = models.ForeignKey('history.App', related_name='sessions')
    client = models.ForeignKey('history.Client',
                               null=True, related_name='sessions') # TODO

    class Meta(object):
        unique_together = ('app', 'key')

    def __unicode__(self):
        return u'{0} on {1}'.format(self.key, self.app)


class ClientRequest(BaseModel):

    PROTOCOLS = (
        ('http', 'HTTP'),
        ('https', 'HTTPS'),
    )

    session = models.ForeignKey('history.ClientSession',
                                related_name='requests')
    remote_addr = models.GenericIPAddressField(db_index=True)
    full_url = models.CharField(max_length=255)
    content = models.TextField()
    # Filled in by save() from full_url, etc. (along with params) --
    method = models.CharField(max_length=10)
    protocol = models.CharField(choices=PROTOCOLS, max_length=5)
    host = models.CharField(max_length=255, db_index=True)
    path = models.CharField(max_length=255, db_index=True)
    user_agent = models.TextField()

    class Meta(object):
        get_latest_by = 'created'

    def __unicode__(self):
        return u'[{0}] {1}'.format(self.remote_addr, self.full_url)

    def parse(self):
        """Parse the raw request content and return the request handler object.

        The handler object has the following attributes of note:

            command: the method of the request
            path: the requested resource path
            request_version: the HTTP version of the request
            headers: a mapping object of the request's headers
            rfile: the raw request buffer

        """
        return util.DumbHTTPRequestHandler(self.content)

    def pre_populate(self):
        """Fill in / update field data derived from ``full_url`` and
        ``content``, namely:

            ``protocol``, ``host``, ``path``, ``method`` and ``user_agent``

        """
        parsed_url = urlparse.urlparse(self.full_url)
        self.protocol = parsed_url.scheme
        self.host = parsed_url.hostname
        self.path = parsed_url.path

        parsed_content = self.parse()
        self.method = parsed_content.command
        self.user_agent = parsed_content.headers.get('User-Agent', '')

    def post_populate(self):
        """Fill in / update associated data derived from ``full_url`` and
        ``content``, namely QueryParameters and FormParameters.

        These data require a ``request_id`` for association, and therefore
        may not be populated prior to insertion, and are handled separately
        from ``pre_populate``.

        """
        parsed = urlparse.urlparse(self.full_url)
        self.query_params.all().delete()
        self.query_params.parse_create(parsed.query)

        additional_payload = self.parse().rfile.read().strip()
        self.form_params.all().delete()
        self.form_params.parse_create(additional_payload)

    def save(self, *args, **kws):
        """Insert/update the object row in the database table.

        Automatically fills in / updates derived fields. (See pre_ and
        post_populate.)

        """
        self.pre_populate()
        super(ClientRequest, self).save(*args, **kws)
        self.post_populate()


class ParameterQuerySet(QuerySet):

    def urlencoded(self):
        return urllib.urlencode(self.values_list('key', 'value'))


class ParameterManager(models.Manager):

    def get_query_set(self):
        return ParameterQuerySet(self.model, using=self._db)

    def parse_create(self, unparsed, request=None):
        parsed = urlparse.parse_qsl(unparsed)
        return [self.create(key=key,
                            value=value,
                            position=position,
                            request=request)
            for position, (key, value) in enumerate(parsed)]

    def urlencoded(self):
        return self.get_query_set().urlencoded()


class RequestParameter(BaseModel):

    key = models.CharField(max_length=255)
    value = models.CharField(max_length=255)
    position = models.PositiveIntegerField()

    objects = ParameterManager()

    class Meta(object):
        abstract = True
        ordering = ('position', 'created')

    def __unicode__(self):
        return u'{0}={1}'.format(self.key, self.value)


class QueryParameter(RequestParameter):

    request = models.ForeignKey('history.ClientRequest',
                                related_name='query_params')

    class Meta(RequestParameter.Meta):
        unique_together = ('request', 'position')


class FormParameter(RequestParameter):

    request = models.ForeignKey('history.ClientRequest',
                                related_name='form_params')

    class Meta(RequestParameter.Meta):
        unique_together = ('request', 'position')


class ServerResponse(BaseModel):

    request = models.OneToOneField('history.ClientRequest')
    # Server may initiate new session via response:
    session = models.ForeignKey('history.ClientSession',
                                related_name='responses')
    content = models.TextField(help_text="The raw, complete response content")
    # Filled in by save() from content --
    status = models.PositiveIntegerField(db_index=True)
    reason = models.CharField(max_length=100)
    body = models.TextField()
    location = models.CharField(max_length=255, null=True, db_index=True,
        help_text="The resource to which the client was redirected, if any")
    # Attached asynchronously --
    captured = models.ImageField(
        upload_to='captures', # TODO
        help_text='The path to an image capture of the rendered response',
    )

    def __unicode__(self):
        return u'{0} {1} {2}'.format(self.request, self.status, self.reason)

    def parse(self):
        """Parse the raw response content and return an httplib response object.

        The response object has the following methods and attributes of note:

            getheaders(): return a mapping of the response headers
            read(): read and return the response payload
            status: the response status code
            reason: the response status reason

        """
        socket = util.FakeSocket(self.content)
        response = httplib.HTTPResponse(socket)
        response.begin()
        return response

    def pre_populate(self):
        """Fill in / update field data derived from ``content``, namely:

            ``status``, ``reason``, ``body`` and ``location``

        """
        response = self.parse()
        self.status = response.status
        self.reason = response.reason
        self.body = response.read()
        self.location = dict(response.getheaders()).get('Location')

    def save(self, *args, **kws):
        """Insert/update the object row in the database table.

        Automatically fills in / updates derived fields. (See pre_populate.)

        """
        self.pre_populate()
        super(ServerResponse, self).save(*args, **kws)


# Automatically create an api key for each new User:
models.signals.post_save.connect(create_api_key, sender=User)
