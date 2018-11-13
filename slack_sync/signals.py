import django.dispatch

# Signal sent after connecting to the server.
after_client_connection = django.dispatch.Signal(providing_args=["client", "startup"])
before_bot_run = django.dispatch.Signal(providing_args=["bot"])
