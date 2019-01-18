from slackbot import bot
from slackbot.dispatcher import MessageDispatcher
from slackbot.manager import PluginsManager

from slack_sync.conf import settings
from slack_sync.slackclient import SlackClient


class Bot(bot.Bot):
    """bot with additional settings"""

    def __init__(self, *args, **kwargs):
        self._client = SlackClient(
            settings.SLACKBOT_API_TOKEN,
            bot_icon=settings.get("BOT_ICON", None),
            bot_emoji=settings.get("BOT_EMOJI", None),
            connect=False
        )
        self._plugins = PluginsManager()
        self._dispatcher = MessageDispatcher(self._client, self._plugins,
                                             settings.ERRORS_TO)
