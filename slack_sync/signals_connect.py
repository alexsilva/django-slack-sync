from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.exceptions import FieldDoesNotExist
from django.db import models
from django.dispatch import receiver
from django.utils.module_loading import import_string

from slack_sync.conf import settings
from .signals import after_client_connection

User = get_user_model()

user_sync_enable = settings.get("SLACK_SYNC_USER_ENABLE", False)
username_callback = settings.get("SLACK_SYNC_USERNAME_CALLBACK",
                                 "slack_sync.callbacks.create_username")
if user_sync_enable:
    username_callback = import_string(username_callback)
user_groups_filters = settings.get("SLACK_SYNC_USER_GROUPS_FILTERS", {})
email_field_name = settings.get("SLACK_SYNC_EMAIL_FIELD_NAME", "email")


@receiver(after_client_connection, dispatch_uid="do-sync-users")
def do_sync_users(sender, **kwargs):
    if not (user_sync_enable or kwargs['startup']):
        # will only synchronize user at boot boot.
        return
    users = kwargs['client'].users
    for pk in users.iterkeys():
        user = users[pk]
        if any([user['deleted'],
                user['is_bot'],
                user['is_app_user']]):
            continue
        user_profile = user['profile']
        defaults = {}

        if 'first_name' in user_profile:
            defaults['first_name'] = user_profile['first_name']
        if 'last_name' in user_profile:
            defaults['last_name'] = user_profile['last_name']

        # Username is not email
        if User.USERNAME_FIELD not in [email_field_name]:
            try:
                field = User._meta.get_field(email_field_name)
                if isinstance(field, models.EmailField) and email_field_name in user_profile:
                    defaults[email_field_name] = user_profile[email_field_name]
            except FieldDoesNotExist:
                pass
        kwargs = {
            User.USERNAME_FIELD: username_callback(user_profile)
        }
        user, created = User.objects.get_or_create(defaults=defaults, **kwargs)
        if user_groups_filters and isinstance(user_groups_filters, dict):
            for group in Group.objects.filter(**user_groups_filters):
                user.groups.add(group)
        # update fields
        if not created:
            for key in defaults.iterkeys():
                setattr(user, key, defaults[key])
            user.save()


def ready(app):
    """no ops"""
