from six import iterkeys
from slackbot import slackclient
from slackbot.dispatcher import unicode_compact

from .signals import after_client_connection


class SlackClient(slackclient.SlackClient):
    """Additional Apis """

    def rtm_connect(self, *args, **kwargs):
        startup = kwargs.pop('startup', False)
        retval = super(SlackClient, self).rtm_connect(*args, **kwargs)
        # Sends a signal after connecting to the server.
        try:
            after_client_connection.send(sender=self.__class__,
                                         client=self,
                                         startup=startup)
        except Exception:
            slackclient.logger.exception("signal after-client-connection")
        return retval

    def open_dm_channel(self, user_id):
        return self.webapi.im.open(user_id).body["channel"]["id"]

    def find_user_by_email(self, email):
        for userid in iterkeys(self.users):
            profile = self.users[userid]['profile']
            if 'email' in profile and profile['email'] == email:
                return userid
        raise ValueError("email '{0!s}' not found!".format(email))

    @unicode_compact
    def send_user_message(self, email, text, **kwargs):
        """
            Sends messages to a user by their email.
            Raises ValueError if email does not exist and errors is True.
        """
        try:
            channel_id = self.open_dm_channel(self.find_user_by_email(email))
            self.rtm_send_message(channel_id, text)
        except ValueError:
            if kwargs.get("errors", False):
                raise
