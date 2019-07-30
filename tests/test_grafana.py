# -*- coding: utf-8 -*-

from chaosk8s_wix.grafana.probes import check_no_alert_for_dashboard,check_service_uppness
from unittest.mock import MagicMock, patch
import json
import responses
import os.path

fake_nasa_url = "http://fakenasa.com/secrets"
fake_grafana_url = "http://fakegrafana.com/"

@responses.activate
def test_check_no_alert_for_dashboard_fails():
    requests_obj = [{
        'evalData' : {
            'evalMatches': [
                {
                    'tags': {
                        'node': {
                            'name': 'some_node_name'
                        }
                    }
                }
            ]
        },
    }]
    responses.add(responses.GET, os.path.join(fake_nasa_url, "grafana"),
                  json={'token': 'FAKE_TOKEN'}, status=200)

    responses.add(responses.GET, os.path.join(fake_grafana_url, "api/alerts"),
                  json=requests_obj, status=200)

    secret_and_config = {
        "NASA_SECRETS_URL": fake_nasa_url,
        "NASA_TOKEN": "fake_token",
        "grafana_host": fake_grafana_url
    }

    retval = check_no_alert_for_dashboard( dashboard_id=1,configuration=secret_and_config, secrets=secret_and_config )
    assert retval == False

@responses.activate
def test_check_no_alert_for_dashboard_success():
    requests_obj = []
    responses.add(responses.GET, os.path.join(fake_nasa_url, "grafana"),
                  json={'token': 'FAKE_TOKEN'}, status=200)

    responses.add(responses.GET, os.path.join(fake_grafana_url, "api/alerts"),
                  json=requests_obj, status=200)

    secret_and_config = {
        "NASA_SECRETS_URL": fake_nasa_url,
        "NASA_TOKEN": "fake_token",
        "grafana_host": fake_grafana_url
    }

    retval = check_no_alert_for_dashboard( dashboard_id=1,configuration=secret_and_config, secrets=secret_and_config )
    assert retval


@responses.activate
def test_check_service_uppness_is_up():
    requests_obj = [{'datapoints':[ (200, 123456),(200, 123457)]}]
    responses.add(responses.GET, os.path.join(fake_nasa_url, "grafana"),
                  json={'token': 'FAKE_TOKEN'}, status=200)

    responses.add(responses.GET, os.path.join(fake_grafana_url, "api/datasources/proxy/1/render"),
                  json=requests_obj, status=200)

    secret_and_config = {
        "NASA_SECRETS_URL": fake_nasa_url,
        "NASA_TOKEN": "fake_token",
        "grafana_host": fake_grafana_url
    }

    retval = check_service_uppness("some_service",configuration=secret_and_config, secrets=secret_and_config, time_interval_seconds=300, allowed_results=[200] )
    assert retval

@responses.activate
def test_check_service_uppness_is_up_fails():

    requests_obj = [{'datapoints':[ (200, 123456),(503, 123457),(200, 123458),(200, 123459)]}]

    responses.add(responses.GET, os.path.join( fake_nasa_url,"grafana" ),
                  json={'token': 'FAKE_TOKEN'}, status=200)

    responses.add(responses.GET, os.path.join(fake_grafana_url, "api/datasources/proxy/1/render"),
                  json=requests_obj, status=200)

    secret_and_config = {
        "NASA_SECRETS_URL": fake_nasa_url,
        "NASA_TOKEN": "fake_token",
        "grafana_host": fake_grafana_url
    }

    retval = check_service_uppness("some_service",configuration=secret_and_config, secrets=secret_and_config, time_interval_seconds=300, allowed_results=[200] )
    assert retval == False