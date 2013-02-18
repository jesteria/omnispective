import urllib

from django.contrib.auth.models import User
from django.db import models
from django.db.models.query import QuerySet
from tastypie.models import create_api_key


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
    linked_sessions = models.ManyToManyField('history.ClientSession') # TODO
    app = models.ForeignKey('history.App', related_name='sessions')
    client = models.ForeignKey('history.Client',
                               null=True, related_name='sessions') # TODO

    class Meta(object):
        unique_together = ('app', 'key')

    def __unicode__(self):
        return u'{0} on {1}'.format(self.key, self.app)


class ClientRequest(BaseModel):

    PROTOCOLS = (
        ('http:', 'HTTP'),
        ('https:', 'HTTPS'),
    )

    session = models.ForeignKey('history.ClientSession',
                                related_name='requests')
    remote_addr = models.GenericIPAddressField(db_index=True)
    encoding = models.CharField(max_length=255)
    method = models.CharField(max_length=10)
    content = models.TextField() # TODO: Should be near-everything (+headers?)
    full_path = models.CharField(max_length=255)
    # TODO: filled in pre_save from full_path (along with params) --
    protocol = models.CharField(choices=PROTOCOLS, max_length=6)
    host = models.CharField(max_length=255, db_index=True)
    path = models.CharField(max_length=255, db_index=True)

    class Meta(object):
        get_latest_by = 'created'

    def __unicode__(self):
        return u'[{0}] {1}'.format(self.remote_addr, self.full_path)


class ParameterQuerySet(QuerySet):

    def urlencoded(self):
        return urllib.urlencode(self.values_list('key', 'value'))


class ParameterManager(models.Manager):

    def get_query_set(self):
#   ...

    def urlencoded(self):
# ...

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
    # generically what we responded with, AND an HTML rendering, (as might not be able to render the same in the future)
    # omniserver should do rendering of response content to image, of course, NOT client
    # and make use of ImageField, i.e. DON'T store image in db
    content = models.TextField()
    request = models.OneToOneField('history.ClientRequest')
    status_code = models.PositiveIntegerField()
    # ...blah blah blah

    def __unicode__(self):
        return u'{0} {1}'.format(self.request, self.status_code)


# Automatically create an api key for each new User:
models.signals.post_save.connect(create_api_key, sender=User)
