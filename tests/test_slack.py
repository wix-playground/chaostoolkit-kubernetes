import requests_mock
from chaosk8s_wix.slack.client import post_message
from unittest.mock import patch
import os


@patch('chaosk8s_wix.slack.logger_handler.get_kube_secret_from_production')
def test_post_message(get_settings):
    fake_settings = {
                        'module': 'chaosslack.notification',
                        'token': 'FAKE_TOKEN',
                        'channel': 'fake-channel'
                    }

    get_settings.return_value = fake_settings
    with requests_mock.mock() as m:
        os.environ['SLACK_CHANNEL'] = 'fake-channel'
        m.post(
            'https://slack.com/api/chat.postMessage',
            status_code=200,
            json={
                "ok": True,
                "channel": "C1H9RESGL",
                "ts": "1503435956.000247"
            }
        )

        post_message(fake_settings,"test")

        assert m.called
        assert m._adapter.last_request.path == "/api/chat.postmessage"
        assert m._adapter.last_request.text.find("channel=%23fake-channel") is not -1
        assert m._adapter.last_request.text.find("text=test") is not -1

