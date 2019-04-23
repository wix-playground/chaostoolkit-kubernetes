from chaosk8s_wix.captains_log.cp_log import publish_to_cp
import responses
import json

@responses.activate
def test_publish_to_cp():
    data = {}

    responses.add(responses.POST, 'https://api.42.wixprod.net/captains-log-web/api/v1/event',
                  json=data, status=200)

    publish_to_cp('https://api.42.wixprod.net/captains-log-web', "Some message")