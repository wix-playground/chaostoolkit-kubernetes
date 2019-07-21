from logging import StreamHandler
from chaosk8s_wix.slack.client import post_message
import logging
import logzero
from chaosk8s_wix import get_kube_secret_from_production
import os

loger_initialized = False

slack_config = None

# Have no access to secrets from random logging. So we rely on env vars


def get_slack_config(secrets):
    env = os.environ
    secrets = secrets or {}

    def lookup(k: str, d: str = None) -> str:
        return secrets.get(k, env.get(k, d))
    prod_vault_url = lookup("NASA_SECRETS_URL", "undefined")
    target_url = os.path.join(prod_vault_url, 'slack')
    token = lookup("NASA_TOKEN", "undefined")
    slack_conf = get_kube_secret_from_production(target_url, token)
    if slack_conf is not None:
        slack_conf['channel'] = lookup("SLACK_CHANNEL", "undefined")
        if slack_conf['channel'] == "undefined":
            slack_conf['channel'] = slack_conf['default_channel']

    return slack_conf


class SlackHanlder(StreamHandler):
    def __init__(self):
        global slack_config
        StreamHandler.__init__(self)
        if slack_config is None:
            slack_config = get_slack_config({})

    def attach(self, logger):
        global loger_initialized
        if not loger_initialized:
            slack_handler = SlackHanlder()
            slack_handler.setLevel(logging.WARNING)
            slack_handler.setFormatter(logzero.LogFormatter(color=False))
            logger.addHandler(slack_handler)

            loger_initialized = True

    def emit(self, record):
        global slack_config
        msg = self.format(record)
        post_message(slack_config, msg)

        # print(">>", msg)
