# -*- coding: utf-8 -*-

from logzero import logger
from slackclient import SlackClient
from chaoslib.settings import load_settings
import os
import socket


__all__ = ["post_message"]


def get_job_url():
    """
    Gets Jenkins job url from JOB_URL env var
    :return: value JOB_URL, if defined, local hostname otherwise
    """
    retval = socket.gethostname()
    val = os.getenv("BUILD_URL")
    if val is not None:
        retval = val
    return retval


def post_message(slack_config, message_text: str = " "):
    """
    Post message to channel defined in chaostoolkit settings file (~/.chaostoolkit/settings.yaml)
    :param message_text: Message text to send
    :return: 0 if everything is ok , error code otherwise
    """
    retval = 1
    settings = slack_config
    if settings is not None and len(settings.keys()) > 0 and "token" in settings.keys():
        retval = 1
        token = settings["token"]
        token = token.strip()
        channel = settings["channel"]
        channel = "#{c}".format(c=channel.lstrip("#").strip())

        sc = SlackClient(token)
        text_to_send = message_text + '\n at ' + get_job_url()
        result = sc.api_call(
            "chat.postMessage",
            channel=channel,
            text=text_to_send,
        )

        if result.get("ok", False) is False:
            print("Sending slack message '{}' failed".format(message_text))
            retval = 1
        else:
            retval = 0
    return retval
