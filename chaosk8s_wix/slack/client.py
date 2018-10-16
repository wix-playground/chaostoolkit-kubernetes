# -*- coding: utf-8 -*-

from logzero import logger
from slackclient import SlackClient
from chaoslib.settings import load_settings
import os
import socket


__all__ = ["post_message", "get_slack_token_from_env"]


def get_job_url():
    """
    Gets Jenkins job url from JOB_URL env var
    :return: value JOB_URL, if defined, local hostname otherwise
    """
    retval = socket.gethostname()
    val = os.getenv("JOB_URL")
    if val is not None:
        retval = val
    return retval


def get_slack_token_from_env(entry) -> str:
    """
    Return slack token. Env variable SLACK_TOKEN will have precedence before any other configuration
    :param entry: current entry with slack configuration from ~/.chaostoolkit/settings.yml
    :return: if SLACK_TOKEN defined, the value of SLACK_TOKEN. token from entry otherwise
    """
    token = ""
    if entry is not None:
        token = entry["token"]
    val = os.getenv("SLACK_TOKEN")
    if val is not None:
        token = val
    return token


def get_settings():
    """
    Gets relevant settings for slack notifications
    :return: dictionary with token and channel for slack notifications
    """
    retval = {}
    settings = load_settings()
    if settings is not None and len(settings.keys()) > 0:
        notifications = settings["notifications"]
        for entry in notifications:
            if entry["module"] == 'chaosslack.notification':
                retval["token"] = get_slack_token_from_env(entry)
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
        text_to_send = message_text + '\n at ' + get_job_url()
        result = sc.api_call(
            "chat.postMessage",
            channel=channel,
            text=text_to_send,
        )

        if result.get("ok", False) is False:
            logger.error("Slack client call failed", result)
            retval = 1
        else:
            retval = 0
    return retval
