from django.conf import settings as django_settings
from django.core.exceptions import ImproperlyConfigured
from slackbot import settings as slackbot_settings


class Settings(object):
    """merge the django settings with the default settings"""

    def __getattr__(self, name):
        if hasattr(django_settings, name):
            return getattr(django_settings, name)
        elif hasattr(slackbot_settings, name):
            return getattr(slackbot_settings, name)
        else:
            raise ImproperlyConfigured('stackbok settings "{0!s}"'.format(name))

    def get(self, name, *args):
        """get name, default or error"""
        try:
            return getattr(self, name)
        except ImproperlyConfigured:
            if args:
                return args[0]
            else:
                raise


# singleton
settings = Settings()
