from django.apps import AppConfig
from django.utils.translation import gettext as _


class SlackSyncApp(AppConfig):
    name = 'slack_sync'
    verbose_name = _("Slack Sync")
