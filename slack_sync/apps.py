from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class SlackSyncApp(AppConfig):
    name = 'slack_sync'
    verbose_name = _("Slack Sync")

    def ready(self):
        from .signals_connect import ready
        ready(self)  # link