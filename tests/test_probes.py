# -*- coding: utf-8 -*-
import io
import json
from unittest.mock import MagicMock, patch
import urllib3

from chaoslib.exceptions import FailedActivity

from kubernetes import client as k8sClient
import pytest

from chaosk8s_wix.probes import all_microservices_healthy, \
    microservice_available_and_healthy, microservice_is_not_available, \
    service_endpoint_is_initialized, deployment_is_not_fully_available, \
    read_microservices_logs, all_pods_in_all_ns_are_ok
from chaosk8s_wix.node.probes import get_active_nodes, all_nodes_are_ok, get_nodes
from chaosk8s_wix.node import load_taint_list_from_dict


def create_node_object(name: str = "default", labels: {} = None) -> k8sClient.V1Node:
    condition = k8sClient.V1NodeCondition(type="Ready", status="True")
    status = k8sClient.V1NodeStatus(conditions=[condition])
    spec = k8sClient.V1NodeSpec(unschedulable=False)
    metadata = k8sClient.V1ObjectMeta(name=name, labels=labels)
    node = k8sClient.V1Node(status=status, spec=spec, metadata=metadata)
    return node


def create_pod_object(name: str = "default", imagename: str = None, labels: {} = None, state: str = "running",
                      namespace: str = "default") -> k8sClient.V1Pod:
    container_state = k8sClient.V1ContainerState(running=MagicMock())
    if state == "terminated":
        container_state = k8sClient.V1ContainerState(terminated=MagicMock())

    image = k8sClient.V1ContainerImage(names=[imagename])
    container_status = k8sClient.V1ContainerStatus(state=container_state, image=image, image_id="fakeimage",
                                                   name="fakename", ready="True", restart_count=0)

    condition = k8sClient.V1PodCondition(type="Ready", status=[container_status])
    status = k8sClient.V1PodStatus(conditions=[condition], container_statuses=[container_status])
    container = k8sClient.V1Container(image=image, name="fakename1")
    spec = k8sClient.V1PodSpec(containers=[container])
    metadata = k8sClient.V1ObjectMeta(name=name, labels=labels, namespace=namespace)
    node = k8sClient.V1Pod(status=status, spec=spec, metadata=metadata)
    return node


@patch('chaosk8s_wix.has_local_config_file', autospec=True)
@patch('chaosk8s_wix.probes.client', autospec=True)
@patch('chaosk8s_wix.client')
def test_unhealthy_system_should_be_reported(cl, client, has_conf):
    has_conf.return_value = False
    pod = MagicMock()
    pod.status.phase = "Failed"

    result = MagicMock()
    result.items = [pod]

    v1 = MagicMock()
    v1.list_namespaced_pod.return_value = result
    client.CoreV1Api.return_value = v1

    with pytest.raises(FailedActivity) as excinfo:
        all_microservices_healthy()
    assert "the system is unhealthy" in str(excinfo)


@patch('chaosk8s_wix.has_local_config_file', autospec=True)
@patch('chaosk8s_wix.probes.client', autospec=True)
@patch('chaosk8s_wix.client')
def test_expecting_a_healthy_microservice_should_be_reported_when_not(cl,
                                                                      client,
                                                                      has_conf):
    has_conf.return_value = False
    result = MagicMock()
    result.items = []

    v1 = MagicMock()
    v1.list_namespaced_deployment.return_value = result
    client.AppsV1beta1Api.return_value = v1

    with pytest.raises(FailedActivity) as excinfo:
        microservice_available_and_healthy("mysvc")
    assert "microservice 'mysvc' was not found" in str(excinfo)

    deployment = MagicMock()
    deployment.spec.replicas = 2
    deployment.status.available_replicas = 1
    result.items.append(deployment)

    with pytest.raises(FailedActivity) as excinfo:
        microservice_available_and_healthy("mysvc")
    assert "microservice 'mysvc' is not healthy" in str(excinfo)


@patch('chaosk8s_wix.has_local_config_file', autospec=True)
@patch('chaosk8s_wix.probes.client', autospec=True)
@patch('chaosk8s_wix.client')
def test_expecting_microservice_is_there_when_it_should_not(cl, client,
                                                            has_conf):
    has_conf.return_value = False
    pod = MagicMock()
    pod.status.phase = "Running"
    result = MagicMock()
    result.items = [pod]

    v1 = MagicMock()
    v1.list_namespaced_pod.return_value = result
    client.CoreV1Api.return_value = v1

    with pytest.raises(FailedActivity) as excinfo:
        microservice_is_not_available("mysvc")
    assert "microservice 'mysvc' is actually running" in str(excinfo)


@patch('chaosk8s_wix.has_local_config_file', autospec=True)
@patch('chaosk8s_wix.probes.client', autospec=True)
@patch('chaosk8s_wix.client')
def test_expecting_service_endpoint_should_be_initialized(cl, client,
                                                          has_conf):
    has_conf.return_value = False
    service = MagicMock()
    result = MagicMock()
    result.items = [service]

    v1 = MagicMock()
    v1.list_namespaced_service.return_value = result
    client.CoreV1Api.return_value = v1

    assert service_endpoint_is_initialized("mysvc") is True


@patch('chaosk8s_wix.has_local_config_file', autospec=True)
@patch('chaosk8s_wix.probes.client', autospec=True)
@patch('chaosk8s_wix.client')
def test_unitialized_or_not_existing_service_endpoint_should_not_be_considered_available(
        cl, client, has_conf):
    has_conf.return_value = False
    service = MagicMock()
    result = MagicMock()
    result.items = []

    v1 = MagicMock()
    v1.list_namespaced_service.return_value = result
    client.CoreV1Api.return_value = v1

    with pytest.raises(FailedActivity) as excinfo:
        service_endpoint_is_initialized("mysvc")
    assert "service 'mysvc' is not initialized" in str(excinfo)


@patch('chaosk8s_wix.has_local_config_file', autospec=True)
@patch('chaosk8s_wix.probes.watch', autospec=True)
@patch('chaosk8s_wix.probes.client', autospec=True)
@patch('chaosk8s_wix.client')
def test_deployment_is_not_fully_available(cl, client, watch, has_conf):
    has_conf.return_value = False
    deployment = MagicMock()
    deployment.spec.replicas = 2
    deployment.status.ready_replicas = 1

    watcher = MagicMock()
    watcher.stream = MagicMock()
    watcher.stream.side_effect = [[{"object": deployment, "type": "ADDED"}]]
    watch.Watch.return_value = watcher

    assert deployment_is_not_fully_available("mysvc") is True


@patch('chaosk8s_wix.has_local_config_file', autospec=True)
@patch('chaosk8s_wix.probes.watch', autospec=True)
@patch('chaosk8s_wix.probes.client', autospec=True)
@patch('chaosk8s_wix.client')
def test_deployment_is_fully_available_when_it_should_not(cl, client,
                                                          watch, has_conf):
    has_conf.return_value = False
    deployment = MagicMock()
    deployment.spec.replicas = 2
    deployment.status.ready_replicas = 2

    watcher = MagicMock()
    watcher.stream = MagicMock()
    watcher.stream.side_effect = urllib3.exceptions.ReadTimeoutError(
        None, None, None)
    watch.Watch.return_value = watcher

    with pytest.raises(FailedActivity) as excinfo:
        deployment_is_not_fully_available("mysvc")
    assert "microservice 'mysvc' failed to stop running within" in str(excinfo)


@patch('chaosk8s_wix.has_local_config_file', autospec=True)
@patch('chaosk8s_wix.pod.probes.client', autospec=True)
@patch('chaosk8s_wix.client')
def test_fetch_last_logs(cl, client, has_conf):
    has_conf.return_value = False
    pod = MagicMock()
    pod.metadata.name = "myapp-1235"
    result = MagicMock()
    result.items = [pod]

    v1 = MagicMock()
    v1.list_namespaced_pod.return_value = result
    client.CoreV1Api.return_value = v1

    v1.read_namespaced_pod_log.return_value = io.BytesIO(b"hello")

    logs = read_microservices_logs("myapp")

    assert pod.metadata.name in logs
    assert logs[pod.metadata.name] == "hello"


@patch('chaosk8s_wix.has_local_config_file', autospec=True)
@patch('chaosk8s_wix.probes.client', autospec=True)
@patch('chaosk8s_wix.client')
def test_can_select_by_label(cl, client, has_conf):
    has_conf.return_value = False
    result = MagicMock()
    result.items = [MagicMock()]

    v1 = MagicMock()
    v1.list_namespaced_service.return_value = result
    client.CoreV1Api.return_value = v1

    label_selector = "app=my-super-app"
    service_endpoint_is_initialized("mysvc", label_selector=label_selector)
    v1.list_namespaced_service.assert_called_with(
        "default", label_selector=label_selector
    )


@patch('chaosk8s_wix.has_local_config_file', autospec=True)
@patch('chaosk8s_wix.node.probes.client', autospec=True)
@patch('chaosk8s_wix.client')
def test_can_select_nodes_by_label(cl, client, has_conf):
    has_conf.return_value = False
    v1 = MagicMock()
    v1.list_node.return_value = io.BytesIO(
        json.dumps({"hey": "there"}).encode('utf-8'))
    client.CoreV1Api.return_value = v1

    label_selector = 'beta.kubernetes.io/instance-type=m5.large'
    resp = get_nodes(label_selector=label_selector)
    v1.list_node.assert_called_with(
        label_selector=label_selector, _preload_content=False)
    assert resp == {"hey": "there"}


@patch('chaosk8s_wix.has_local_config_file', autospec=True)
@patch('chaosk8s_wix.node.client', autospec=True)
@patch('chaosk8s_wix.client')
def test_all_nodes_are_ok(cl, client, has_conf):
    has_conf.return_value = False
    v1 = MagicMock()

    node = create_node_object("fakenode")

    response = k8sClient.V1NodeList(items=[node])

    v1.list_node_with_http_info.return_value = response
    client.CoreV1Api.return_value = v1

    label_selector = 'beta.kubernetes.io/instance-type=m5.large'
    resp = all_nodes_are_ok(label_selector=label_selector)
    v1.list_node_with_http_info.assert_called_with(
        label_selector=label_selector, _preload_content=True, _return_http_data_only=True)
    assert resp is True


@patch('chaosk8s_wix.has_local_config_file', autospec=True)
@patch('chaosk8s_wix.probes.client', autospec=True)
@patch('chaosk8s_wix.client')
def test_all_pods_in_all_ns_are_ok(cl, client, has_conf):
    has_conf.return_value = False
    v1 = MagicMock()

    pod1 = create_pod_object("fakepod1")
    pod2 = create_pod_object("fakepod2")

    response = k8sClient.V1PodList(items=[pod1, pod2])
    v1.list_pod_for_all_namespaces.return_value = response
    client.CoreV1Api.return_value = v1

    resp = all_pods_in_all_ns_are_ok(ns_ignore_list=["db-catalog"])
    v1.list_pod_for_all_namespaces.assert_called_with(watch=False)
    assert resp is True


@patch('chaosk8s_wix.has_local_config_file', autospec=True)
@patch('chaosk8s_wix.probes.client', autospec=True)
@patch('chaosk8s_wix.client')
def test_all_pods_in_all_ns_are_ok_failure(cl, client, has_conf):
    has_conf.return_value = False
    v1 = MagicMock()

    pod1 = create_pod_object("fakepod1")
    pod2 = create_pod_object("fakepod2", state="terminated")
    pod2.status.container_statuses[0].running = None

    response = k8sClient.V1PodList(items=[pod1, pod2])
    v1.list_pod_for_all_namespaces.return_value = response
    client.CoreV1Api.return_value = v1

    resp = all_pods_in_all_ns_are_ok(ns_ignore_list=["db-catalog"])
    v1.list_pod_for_all_namespaces.assert_called_with(watch=False)
    assert resp is False


@patch('chaosk8s_wix.has_local_config_file', autospec=True)
@patch('chaosk8s_wix.probes.client', autospec=True)
@patch('chaosk8s_wix.client')
def test_all_pods_in_all_ns_are_ok_ignore(cl, client, has_conf):
    has_conf.return_value = False
    v1 = MagicMock()

    pod1 = create_pod_object("fakepod1")
    pod2 = create_pod_object("fakepod2", state="terminated", namespace="db-catalog")

    response = k8sClient.V1PodList(items=[pod1, pod2])
    v1.list_pod_for_all_namespaces.return_value = response
    client.CoreV1Api.return_value = v1

    resp = all_pods_in_all_ns_are_ok(ns_ignore_list=["db-catalog"])
    v1.list_pod_for_all_namespaces.assert_called_with(watch=False)
    assert resp is True


@patch('chaosk8s_wix.has_local_config_file', autospec=True)
@patch('chaosk8s_wix.node.client', autospec=True)
@patch('chaosk8s_wix.client')
def test_get_non_tainted_nodes(cl, client, has_conf):
    has_conf.return_value = False
    v1 = MagicMock()

    node1 = create_node_object("tainted_node")
    taint = k8sClient.V1Taint(effect="NoSchedule", key="faketaint", time_added=None, value=None)
    node1.spec.taints = [taint]
    node2 = create_node_object("not_tainted_node")

    response = k8sClient.V1NodeList(items=[node1, node2])
    v1.list_node_with_http_info.return_value = response
    client.CoreV1Api.return_value = v1
    client.V1NodeList.return_value = k8sClient.V1NodeList(items=[])
    resp, v1 = get_active_nodes()
    assert len(resp.items) == 2


@patch('chaosk8s_wix.has_local_config_file', autospec=True)
@patch('chaosk8s_wix.node.client', autospec=True)
@patch('chaosk8s_wix.client')
def test_get_non_tainted_nodes_filtered(cl, client, has_conf):
    has_conf.return_value = False
    v1 = MagicMock()

    taint1 = k8sClient.V1Taint(effect="NoSchedule", key="node-role.kubernetes.io/master", value=None, time_added=None)
    taint2 = k8sClient.V1Taint(effect="NoSchedule", key="dedicated", value="spot", time_added=None)

    ignore_list = [taint1, taint2]

    node1 = create_node_object("tainted_node")
    taint = k8sClient.V1Taint(effect="NoSchedule", key="faketaint", time_added=None, value=None)
    node1.spec.taints = [taint]

    node2 = create_node_object("tainted_node_ignore")
    taint = k8sClient.V1Taint(effect="NoSchedule", key="dedicated", time_added=None, value="spot")
    node2.spec.taints = [taint]

    node3 = create_node_object("not_tainted")

    response = k8sClient.V1NodeList(items=[node1, node2, node3])
    v1.list_node_with_http_info.return_value = response
    client.CoreV1Api.return_value = v1
    client.V1NodeList.return_value = k8sClient.V1NodeList(items=[])

    resp, v1 = get_active_nodes(taints_ignore_list=ignore_list)
    assert 2 == len(resp.items)
