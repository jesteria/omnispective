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


class QSItem(BaseModel):

    key = models.CharField(max_length=255)
    value = models.CharField(max_length=255)
    request = models.ForeignKey('history.ClientRequest',
                                related_name='qs_items')

    def __unicode__(self):
        return u'{0}={1}'.format(self.key, self.value)


class ClientRequest(BaseModel):

    PROTOCOLS = (
        ('http:', 'HTTP'),
        ('https:', 'HTTPS'),
    )

    raw = models.TextField()
    method = models.CharField(max_length=10)
    protocol = models.CharField(choices=PROTOCOLS, max_length=6)
    host = models.CharField(max_length=255, db_index=True)
    path = models.CharField(max_length=255, db_index=True)
    full_path = models.CharField(max_length=255)
    session = models.CharField(max_length=255, db_index=True)
    remote_addr = models.GenericIPAddressField(db_index=True)
    # ...blah blah blah

    class Meta(object):
        get_latest_by = 'created'

    def __unicode__(self):
        return u'[{0}] {1}'.format(self.remote_addr, self.full_path)


models.signals.post_save.connect(create_api_key, sender=User)
