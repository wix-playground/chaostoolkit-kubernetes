import requests
import requests_mock
from chaosk8s_wix.slack.client import post_message


def test_post_message():
    with requests_mock.mock() as m:
        m.post(
            'https://slack.com/api/chat.postMessage',
            status_code=200,
            json={
                "ok": True,
                "channel": "C1H9RESGL",
                "ts": "1503435956.000247"
            }
        )

        post_message("test")

        assert m.called
        assert m._adapter.last_request.path == "/api/chat.postmessage"
        assert m._adapter.last_request.text == "channel=%23sphera-urgent&text=test"
