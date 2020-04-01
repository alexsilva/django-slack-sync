import json
import unittest

import mock


@mock.patch("websocket.create_connection")
@mock.patch("websocket.WebSocket")
@mock.patch("select.select")
class SlackBotClientTests(unittest.TestCase):

    def setUp(self):
        from slack_sync.slackclient import SlackClient
        from slack_sync.conf import settings

        self.client = SlackClient(settings.SLACKBOT_API_TOKEN,
                                  connect=False)

    def test_websocket_safe_read(self, select, WebSocket, create_connection):
        websock = WebSocket.return_value

        create_connection.return_value = websock

        select.return_value = [websock.sock], [], []

        def socket_recv():
            buff = json.dumps({'hello': True})
            select.return_value = [], [], []
            return buff

        websock.recv = socket_recv

        self.client.rtm_connect()

    def test_ping(self, select, WebSocket, create_connection):
        websock = WebSocket.return_value

        create_connection.return_value = websock

        select.return_value = [websock.sock], [], []

        def socket_recv():
            args, kwargs = websock.send.call_args
            send_data = json.loads(args[0])

            buff = json.dumps({'type': 'pong',
                               'reply_to': send_data['id']})
            select.return_value = [], [], []
            return buff

        websock.recv = socket_recv

        self.assertTrue(self.client.ping())
