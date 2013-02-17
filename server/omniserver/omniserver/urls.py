from django.conf.urls import patterns, include, url

from history import api


urlpatterns = patterns('',
    (r'^api/', include(api.ClientRequestResource().urls)),
    (r'^api/', include(api.ClientSessionResource().urls)),
    (r'^api/', include(api.AppResource().urls)),
)
