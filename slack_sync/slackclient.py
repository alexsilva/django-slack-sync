from slackbot import slackclient

from .signals import after_client_connection


class SlackClient(slackclient.SlackClient):
    """Additional Apis """

    def rtm_connect(self, *args, **kwargs):
        retval = super(SlackClient, self).rtm_connect(*args, **kwargs)
        # Sends a signal after connecting to the server.
        after_client_connection.send(sender=self.__class__,
                                     client=self)
        return retval
