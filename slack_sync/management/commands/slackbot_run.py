# coding=utf-8
import logging
import sys

from django.core.management import BaseCommand
from django.utils.translation import gettext_lazy as _

from slack_sync.bot import Bot
from slack_sync.signals import before_bot_run


class Command(BaseCommand):
    help = _("""Slackboot Server""")

    LOGGER_FORMAT = '[%(asctime)s: %(levelname)s/%(name)s] %(message)s'

    @classmethod
    def setup_loggers(cls):
        """slackbot logger setup"""
        shandler = logging.StreamHandler(sys.stdout)
        shandler.setLevel(logging.DEBUG)

        # create formatter
        formatter = logging.Formatter(cls.LOGGER_FORMAT)

        # add formatter to ch
        shandler.setFormatter(formatter)

        # add ch to logger
        for name in ('slackbot.slackclient',
                     'slackbot.bot'):
            logger = logging.getLogger(name)
            logger.setLevel(logging.DEBUG)
            logger.addHandler(shandler)

    def handle(self, *args, **options):
        self.setup_loggers()
        # slackbot server
        bot = Bot()
        before_bot_run.send(sender=self.__class__,
                            bot=bot)
        bot.run()
