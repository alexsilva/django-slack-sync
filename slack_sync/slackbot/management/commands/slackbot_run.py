# coding=utf-8
from django.utils.translation import gettext as _
from slackbot.bot import Bot


class Command(BaseCommandUnicode):
    help = _("""Slackboot server""")

    def handle(self, *args, **options):
        # slackbot server
        bot = Bot()
        bot.run()
