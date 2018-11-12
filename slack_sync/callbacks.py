from django.contrib.auth import get_user_model
from django.db import models

from .conf import settings

username_prefix = settings.get("SLACKBOT_USERNAME_PREFIX", "slackbot")

User = get_user_model()


def create_username(user_profile):
    """builds an appropriate name for the user"""
    field = User._meta.get_field(User.USERNAME_FIELD)
    if isinstance(field, models.EmailField):
        return user_profile['email']
    else:
        return u"{0:s}-{1[display_name_normalized]}".format(username_prefix, user_profile)
