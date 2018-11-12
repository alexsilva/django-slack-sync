# coding=utf-8
from django.core.management import BaseCommand
from django.utils.translation import gettext_lazy as _

from slack_sync.bot import Bot
from slack_sync.signals import before_bot_run


class Command(BaseCommand):
    help = _("""Slackboot Server""")

    def handle(self, *args, **options):
        # slackbot server
        bot = Bot()
        before_bot_run.send(sender=self.__class__,
                            bot=bot)
        bot.run()
