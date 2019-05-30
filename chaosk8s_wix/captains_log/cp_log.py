import requests
import json
import datetime


def urljoin(*args):
    return "/".join(map(lambda x: str(x).rstrip('/'), args))


def publish_to_cp(server_url, message: str):
    '''publish message to captain's log'''
    headers = {'content-type': 'application/json'}
    url = urljoin(server_url, 'api/v1/event')
    # url = "https://api.42.wixprod.net/captains-log-web/api/v1/event"

    body = {
        "actionName": "action_performed",
        "biEventId": 10,
        "datetime": str(datetime.datetime.now()),
        "eventOrigin": "chaos",
        "extraFields": {},
        "summary": message,
        "userEmail": "somebody@wix.com"
    }

    r = requests.post(url, headers=headers, data=body)
    if r.status_code == 200:
        json_data = json.loads(r.text)
    else:
        raise requests.exceptions.RequestException(
            '{}:{}'.format(r.status_code, r.reason))
    return json_data
