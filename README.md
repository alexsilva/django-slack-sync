
Settings
-
`SLACK_SYNC_USER_ENABLE`: Enable slack user synchronization.

`SLACK_SYNC_USER_GROUPS_FILTERS`: Dictionary with group filters 
 `{'name': 'mygroup}`

Send a message to a user by email
-

```
from slack_sync.conf import settings as slack_sync_settings

client = SlackClient(slack_sync_settings.SLACKBOT_API_TOKEN)

client.send_user_message('user@gmail.com',
                         u"some mensage",
                         errors=True)
```