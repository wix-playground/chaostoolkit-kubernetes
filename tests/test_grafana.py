# -*- coding: utf-8 -*-

from chaosk8s_wix.grafana.probes import check_no_alert_for_dashboard,check_service_uppness
from unittest.mock import MagicMock, patch
import json

@patch('chaosk8s_wix.grafana.probes.requests')
def test_check_no_alert_for_dashboard_fails(requests):
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
    fake_response = MagicMock()
    fake_response.json.return_value = requests_obj
    requests.get.return_value = fake_response

    secret_and_confifg = {
    }

    retval = check_no_alert_for_dashboard(panel_id=1, dashboard_id=1,configuration=secret_and_confifg, secrets=secret_and_confifg )
    assert retval == False

@patch('chaosk8s_wix.grafana.probes.requests')
def test_check_no_alert_for_dashboard_success(requests):
    requests_obj = []
    fake_response = MagicMock()
    fake_response.json.return_value = requests_obj
    requests.get.return_value = fake_response

    secret_and_confifg = {
    }

    retval = check_no_alert_for_dashboard(panel_id=1, dashboard_id=1,configuration=secret_and_confifg, secrets=secret_and_confifg )
    assert retval


@patch('chaosk8s_wix.grafana.probes.requests')
def test_check_service_uppness_is_up(requests):

    requests_obj = [{'datapoints':[ (200, 123456),(200, 123457)]}]
    fake_response = MagicMock()
    fake_response.text = json.dumps(requests_obj)
    requests.get.return_value = fake_response

    secret_and_config = {
    }

    retval = check_service_uppness("some_service",configuration=secret_and_config, secrets=secret_and_config, time_interval_seconds=300, allowed_results=[200] )
    assert retval

@patch('chaosk8s_wix.grafana.probes.requests')
def test_check_service_uppness_is_up_fails(requests):

    requests_obj = [{'datapoints':[ (200, 123456),(503, 123457),(200, 123458),(200, 123459)]}]
    fake_response = MagicMock()
    fake_response.text = json.dumps(requests_obj)
    requests.get.return_value = fake_response

    secret_and_config = {
    }

    retval = check_service_uppness("some_service",configuration=secret_and_config, secrets=secret_and_config, time_interval_seconds=300, allowed_results=[200] )
    assert retval == False