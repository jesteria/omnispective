from django.conf.urls.defaults import url
from tastypie import exceptions, fields
from tastypie.authentication import ApiKeyAuthentication
from tastypie.authorization import DjangoAuthorization
from tastypie.resources import ModelResource

from history import models as history


class AppResource(ModelResource):

    class Meta(object):
        authentication = ApiKeyAuthentication()
        queryset = history.App.objects.all()
        list_allowed_methods = detail_allowed_methods = ['get']

    def prepend_urls(self):
        # Allow get app detail by code rather than PK:
        detail_pattern = r"^(?P<resource_name>{0})/(?P<code>[-\w]+)/$".format(
            self._meta.resource_name)
        return [
            url(detail_pattern,
                self.wrap_view('dispatch_detail'), name="api_dispatch_detail"),
        ]


class ClientSessionResource(ModelResource):

    app = fields.ToOneField(AppResource, 'app')

    def hydrate_app(self, bundle):
        # Allow specification of app by code:
        if not bundle.obj.app_id:
            try:
                app_code = bundle.data.pop('app')
                app = history.App.objects.get(code=app_code)
            except (KeyError, history.App.DoesNotExist):
                raise exceptions.BadRequest("App code missing or invalid")
            else:
                bundle.obj.app = app
        return bundle

    class Meta(object):
        authentication = ApiKeyAuthentication()
        authorization = DjangoAuthorization()
        queryset = history.ClientSession.objects.all()


class ClientRequestResource(ModelResource):

    session = fields.ToOneField(ClientSessionResource, 'session')

    class Meta(object):
        authentication = ApiKeyAuthentication()
        authorization = DjangoAuthorization()
        queryset = history.ClientRequest.objects.all()
