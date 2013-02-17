from history import models as history
from tastypie.authentication import ApiKeyAuthentication
from tastypie.authorization import DjangoAuthorization
from tastypie.resources import ModelResource


class ClientRequestResource(ModelResource):

    class Meta(object):
        authentication = ApiKeyAuthentication()
        authorization = DjangoAuthorization()
        queryset = history.ClientRequest.objects.all()
