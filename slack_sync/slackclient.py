# coding=utf-8
import os
import random
import socket
import ssl
import time
from select import select
from ssl import SSLError
import errno
import requests
import slacker
from django.utils.functional import cached_property
from six import iterkeys
from slackbot import slackclient
from slackbot.dispatcher import unicode_compact
from websocket import WebSocketException, WebSocketConnectionClosedException, create_connection

from .signals import after_client_connection


class SlackClient(slackclient.SlackClient):
    """Additional Apis """

    def __init__(self, *args, **kwargs):
        self.websocket_options = kwargs.pop("websocket_options", {})
        self.websocket_options.setdefault("timeout", 5.0)
        self.reconnect_options = kwargs.pop("reconnect_options", {})
        self.reconnect_options.setdefault("retry", 5)
        self.reconnect_options.setdefault("delay", 15.0)
        super(SlackClient, self).__init__(*args, **kwargs)
        self.session = requests.session()
        self.webapi = slacker.Slacker(self.token, session=self.session)

    def parse_slack_login_data(self, login_data):
        self.login_data = login_data
        self.domain = self.login_data['team']['domain']
        self.username = self.login_data['self']['name']
        self.parse_user_data(login_data['users'])
        self.parse_channel_data(login_data['channels'])
        self.parse_channel_data(login_data['groups'])
        self.parse_channel_data(login_data['ims'])

        proxy, proxy_port, no_proxy = None, None, None
        if 'http_proxy' in os.environ:
            proxy, proxy_port = os.environ['http_proxy'].split(':')
        if 'no_proxy' in os.environ:
            no_proxy = os.environ['no_proxy']

        self.websocket = create_connection(
            self.login_data['url'],
            http_proxy_host=proxy,
            http_proxy_port=proxy_port,
            http_no_proxy=no_proxy,
            **self.websocket_options
        )
        self.websocket.sock.setblocking(0)
        # with reconnect = True we fall into a kind of recursion
        self.websocket_safe_read(reconnect=False)  # socket flush

    def reconnect(self):
        index = 0
        if self.websocket_live:
            try:
                self.websocket.close()
            except Exception as err:
                self.logger.error("websocket close exception: %r" % err)
        while index < self.reconnect_options['retry']:
            try:
                self.rtm_connect()
                self.logger.warning('reconnected to slack rtm websocket')
                return
            except Exception as e:
                index += 1
                self.logger.exception('failed to reconnect: %s', e)
                time.sleep(self.reconnect_options['delay'])

    def websocket_safe_read(self, reconnect=True):
        """Returns data if available, otherwise ''. Newlines indicate multiple messages """
        data = ''
        while True:
            try:
                websocket = self.websocket.sock
                rsocks, wsocks, xsocks = select([websocket], [], [websocket],
                                                self.websocket.timeout)
                assert len(xsocks) == 0, 'socket (%r) dead!' % websocket
                if websocket not in rsocks:
                    break
            except Exception as err:
                self.logger.warning('Exception in select socket: %r', err)
                if not reconnect:
                    break
                self.reconnect()
                break
            try:
                data += "{0}\n".format(self.websocket.recv())
            except WebSocketException as err:
                if isinstance(err, WebSocketConnectionClosedException):
                    self.logger.warning('Lost websocket connection, try to reconnect now')
                else:
                    self.logger.warning('Websocket exception: %s', err)
                if not reconnect:
                    break
                self.reconnect()
                break
            except SSLError as err:
                if err.errno != ssl.SSL_ERROR_WANT_READ:
                    self.logger.warning('SSLError in websocket_safe_read: %s', err)
                break
            except socket.error as err:
                if reconnect and err.errno in (errno.ECONNRESET,):
                    self.logger.info("ECONNRESET reconnecting...")
                    self.reconnect()
                    break
            except Exception as e:
                self.logger.warning('Exception in websocket_safe_read: %s', e)
                break
        return data.strip()

    @cached_property
    def logger(self):
        """slackclient logger"""
        return slackclient.logger

    @property
    def websocket_live(self):
        return self.websocket is not None and \
               self.websocket.connected

    def ping(self):
        if not self.websocket_live:
            # No connection was started yet
            return False
        reply_id = random.randint(1, 2048)
        self.send_to_websocket({'type': 'ping', 'id': reply_id})
        for response in self.rtm_read():
            if response['type'] == "pong" and response['reply_to'] == reply_id:
                return True
        return False

    def rtm_smart_connect(self, *args, **kwargs):
        """It only runs a new connection when ping fails"""
        self.connected = self.ping()
        if not self.connected:
            self.rtm_connect(*args, **kwargs)

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
            self.websocket_safe_read()
        except ValueError:
            if kwargs.get("errors", False):
                raise
