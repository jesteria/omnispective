import django.conf

from omniclient import Defaults


class Settings(Defaults):

    USE_CELERY = 'djcelery' in django.conf.settings.INSTALLED_APPS

    def __getattribute__(self, key):
        external_key = 'OMNISPECTIVE_{0}'.format(key)
        try:
            return getattr(django.conf.settings, external_key)
        except AttributeError as error:
            try:
                return getattr(type(self), key)
            except AttributeError:
                raise error

settings = Settings()
