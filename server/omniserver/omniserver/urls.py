from django.conf.urls import patterns, include, url

from history import api


urlpatterns = patterns('',
    (r'^api/', include(api.ClientRequestResource().urls)),
)
