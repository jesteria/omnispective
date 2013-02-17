from django.contrib.auth.models import User
from django.db import models
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

    app = models.ForeignKey('history.App')
    username = models.CharField(max_length=200, db_index=True)

    class Meta(object):
        unique_together = ('app', 'username')

    def __unicode__(self):
        return u'{0} on {1}'.format(self.username, self.app)


class ClientSession(BaseModel):

    key = models.CharField(max_length=255, db_index=True)
    linked_sessions = models.ManyToManyField('history.ClientSession')
    app = models.ForeignKey('history.App', related_name='sessions')
    client = models.ForeignKey('history.Client', null=True)

    class Meta(object):
        unique_together = ('app', 'key')

    def __unicode__(self):
        return u'{0} on {1}'.format(self.key, self.app)


class ClientRequest(BaseModel):

    PROTOCOLS = (
        ('http:', 'HTTP'),
        ('https:', 'HTTPS'),
    )

    content = models.TextField()
    method = models.CharField(max_length=10)
    protocol = models.CharField(choices=PROTOCOLS, max_length=6)
    host = models.CharField(max_length=255, db_index=True)
    path = models.CharField(max_length=255, db_index=True)
    full_path = models.CharField(max_length=255)
    remote_addr = models.GenericIPAddressField(db_index=True)
    session = models.ForeignKey('history.ClientSession',
                                related_name='requests')
    # ...blah blah blah

    class Meta(object):
        get_latest_by = 'created'

    def __unicode__(self):
        return u'[{0}] {1}'.format(self.remote_addr, self.full_path)


class QSItem(BaseModel):

    key = models.CharField(max_length=255)
    value = models.CharField(max_length=255)
    request = models.ForeignKey('history.ClientRequest',
                                related_name='qs_items')

    def __unicode__(self):
        return u'{0}={1}'.format(self.key, self.value)


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
