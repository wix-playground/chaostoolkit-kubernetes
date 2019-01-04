# -*- coding: utf-8 -*-

from unittest.mock import MagicMock, patch, ANY
from chaoslib.exceptions import FailedActivity,ActivityFailed
import pytest

from chaosk8s_wix.pod.actions import terminate_pods
from chaosk8s_wix.pod.probes import pods_in_phase, pods_not_in_phase,verify_pod_termination_reason


@patch('chaosk8s_wix.has_local_config_file', autospec=True)
@patch('chaosk8s_wix.pod.actions.client', autospec=True)
@patch('chaosk8s_wix.client')
def test_terminate_pods_by_name_pattern(cl, client, has_conf):
    has_conf.return_value = False
    pod = MagicMock()
    pod.metadata.name = "my-app-1"

    pod2 = MagicMock()
    pod2.metadata.name = "some-db"

    result = MagicMock()
    result.items = [pod, pod2]

    v1 = MagicMock()
    v1.list_namespaced_pod.return_value = result
    client.CoreV1Api.return_value = v1

    terminate_pods(name_pattern="my-app-[0-9]$")
    v1.delete_namespaced_pod.assert_called_with(
        pod.metadata.name, "default", ANY)


@patch('chaosk8s_wix.has_local_config_file', autospec=True)
@patch('chaosk8s_wix.pod.probes.client', autospec=True)
@patch('chaosk8s_wix.client')
def test_pods_in_phase(cl, client, has_conf):
    has_conf.return_value = False
    pod = MagicMock()
    pod.status = MagicMock()
    pod.status.phase = "Running"
    result = MagicMock()
    result.items = [pod]

    v1 = MagicMock()
    v1.list_namespaced_pod.return_value = result
    client.CoreV1Api.return_value = v1

    assert pods_in_phase(label_selector="app=mysvc", phase="Running") is True


@patch('chaosk8s_wix.has_local_config_file', autospec=True)
@patch('chaosk8s_wix.pod.probes.client', autospec=True)
@patch('chaosk8s_wix.client')
def test_pods_should_have_been_phase(cl, client, has_conf):
    has_conf.return_value = False
    pod = MagicMock()
    pod.status = MagicMock()
    pod.status.phase = "Pending"
    result = MagicMock()
    result.items = [pod]

    v1 = MagicMock()
    v1.list_namespaced_pod.return_value = result
    client.CoreV1Api.return_value = v1

    with pytest.raises(FailedActivity) as x:
        assert pods_in_phase(
            label_selector="app=mysvc", phase="Running") is True
    assert "pod 'app=mysvc' is in phase 'Pending' but should be " \
           "'Running'" in str(x)


@patch('chaosk8s_wix.has_local_config_file', autospec=True)
@patch('chaosk8s_wix.pod.probes.client', autospec=True)
@patch('chaosk8s_wix.client')
def test_pods_not_in_phase(cl, client, has_conf):
    has_conf.return_value = False
    pod = MagicMock()
    pod.status = MagicMock()
    pod.status.phase = "Pending"
    result = MagicMock()
    result.items = [pod]

    v1 = MagicMock()
    v1.list_namespaced_pod.return_value = result
    client.CoreV1Api.return_value = v1

    assert pods_not_in_phase(
        label_selector="app=mysvc", phase="Running") is True


@patch('chaosk8s_wix.has_local_config_file', autospec=True)
@patch('chaosk8s_wix.pod.probes.client', autospec=True)
@patch('chaosk8s_wix.client')
def test_verify_pod_termination_reason_we_have_oom(cl, client, has_conf):
    has_conf.return_value = False
    pod = MagicMock()
    pod.status = MagicMock()

    status = MagicMock()
    status.last_state = MagicMock()
    status.last_state.terminated = MagicMock()
    status.last_state.terminated.reason = 'OOMKilled'
    pod.status.container_statuses = [status]
    result = MagicMock()
    result.items = [pod]

    v1 = MagicMock()
    v1.list_pod_for_all_namespaces.return_value = result
    client.CoreV1Api.return_value = v1
    result = verify_pod_termination_reason("somelabel" , "OOMKilled")
    assert result is True


@patch('chaosk8s_wix.has_local_config_file', autospec=True)
@patch('chaosk8s_wix.pod.probes.client', autospec=True)
@patch('chaosk8s_wix.client')
def test_verify_pod_termination_reason_no_pods(cl, client, has_conf):
    has_conf.return_value = False

    result = MagicMock()
    result.items = []

    v1 = MagicMock()
    v1.list_pod_for_all_namespaces.return_value = result
    client.CoreV1Api.return_value = v1
    with pytest.raises(FailedActivity):
        verify_pod_termination_reason("somelabel" , "OOMKilled")
    

@patch('chaosk8s_wix.has_local_config_file', autospec=True)
@patch('chaosk8s_wix.pod.probes.client', autospec=True)
@patch('chaosk8s_wix.client')
def test_verify_pod_termination_reason_we_have_is_healthy(cl, client, has_conf):
    has_conf.return_value = False
    pod = MagicMock()
    pod.status = MagicMock()

    status = MagicMock()
    status.last_state = MagicMock()
    status.last_state.terminated = None

    pod.status.container_statuses = [status]
    result = MagicMock()
    result.items = [pod]

    v1 = MagicMock()
    v1.list_pod_for_all_namespaces.return_value = result
    client.CoreV1Api.return_value = v1

    with pytest.raises(FailedActivity) :
        verify_pod_termination_reason("somelabel" , "OOMKilled")
