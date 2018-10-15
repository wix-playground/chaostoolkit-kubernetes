# -*- coding: utf-8 -*-

from logzero import logger
from slackclient import SlackClient
from chaoslib.settings import load_settings

__all__ = ["post_message"]

someshit
def get_settings():
    """
    Gets relevant settings for slack notifications
    :return: dictionary with token and channel for slack notifications
    """
    retval = {}
    settings = load_settings()
    notifications = settings["notifications"]
    for entry in notifications:
        if entry["module"] == 'chaosslack.notification':
            retval["token"] = entry["token"]
            retval["channel"] = entry["channel"]
            break

    return retval


def post_message(message_text):
    """
    Post message to channel defined in chaostoolkit settings file (~/.chaostoolkit/settings.yaml)
    :param message_text: Message text to send
    :return: 0 if everything is ok , error code otherwise
    """
    logger.debug("Slack Client: post_message called " + message_text)
    retval = 1
    settings = get_settings()
    if settings is not None and len(settings.keys()) > 0:
        retval = 1
        token = settings["token"]
        token = token.strip()
        channel = settings["channel"]
        channel = "#{c}".format(c=channel.lstrip("#").strip())

        sc = SlackClient(token)
        result = sc.api_call(
            "chat.postMessage",
            channel=channel,
            text=message_text,
        )

        if result.get("ok", False) is False:
            logger.error("Slack client call failed")
            retval = 1
    return retval
