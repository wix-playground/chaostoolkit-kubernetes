# -*- coding: utf-8 -*-
from unittest.mock import ANY, MagicMock, patch

from chaoslib.exceptions import FailedActivity
from kubernetes import client as k8sClient
from kubernetes import config
from kubernetes.client.rest import ApiException
import pytest

from chaosk8s_wix.actions import start_microservice, kill_microservice
from chaosk8s_wix.node.actions import cordon_node, create_node, delete_nodes, \
    uncordon_node, drain_nodes,remove_label_from_node, taint_node, add_label_to_node


@patch('chaosk8s_wix.has_local_config_file', autospec=True)
def test_cannot_process_other_than_yaml_and_json(has_conf):
    has_conf.return_value = False
    path = "./tests/fixtures/invalid-k8s.txt"
    with pytest.raises(FailedActivity) as excinfo:
        start_microservice(spec_path=path)
    assert "cannot process {path}".format(path=path) in str(excinfo)


@patch('chaosk8s_wix.has_local_config_file', autospec=True)
@patch('chaosk8s_wix.node.actions.client', autospec=True)
@patch('chaosk8s_wix.client')
def test_create_node(cl, client, has_conf):
    has_conf.return_value = False

    meta = {
        "cluster_name": "somevalue"
    }

    spec = {
        "external_id": "somemetavalue"
    }

    node = MagicMock()
    node.metadata.name = "mynode"

    v1 = MagicMock()
    v1.create_node.return_value = node
    client.CoreV1Api.return_value = v1

    res = create_node(meta, spec)
    assert res.metadata.name == "mynode"


@patch('chaosk8s_wix.has_local_config_file', autospec=True)
@patch('chaosk8s_wix.node.actions.client', autospec=True)
@patch('chaosk8s_wix.client')
def test_create_node_may_fail(cl, client, has_conf):
    has_conf.return_value = False

    meta = {
        "cluster_name": "somevalue"
    }

    spec = {
        "external_id": "somemetavalue"
    }

    v1 = MagicMock()
    v1.create_node.side_effect = ApiException()
    client.CoreV1Api.return_value = v1

    with pytest.raises(FailedActivity) as x:
        create_node(meta, spec)
    assert "Creating new node failed" in str(x)


@patch('chaosk8s_wix.has_local_config_file', autospec=True)
@patch('chaosk8s_wix.node.actions.client', autospec=True)
@patch('chaosk8s_wix.client')
def test_delete_nodes(cl, client, has_conf):
    has_conf.return_value = False

    v1 = MagicMock()
    client.CoreV1Api.return_value = v1

    node = MagicMock()
    node.metadata.name = "mynode"

    result = MagicMock()
    result.items = [node]
    v1.list_node.return_value = result

    res = MagicMock()
    res.status = "Success"
    v1.delete_node.return_value = res

    delete_nodes(label_selector="k=mynode")

    v1.delete_node.assert_called_with("mynode", ANY, grace_period_seconds=None)


@patch('chaosk8s_wix.has_local_config_file', autospec=True)
@patch('chaosk8s_wix.node.actions.client', autospec=True)
@patch('chaosk8s_wix.client')
def test_delete_nodes(cl, client, has_conf):
    has_conf.return_value = False

    v1 = MagicMock()
    client.CoreV1Api.return_value = v1

    node = MagicMock()
    node.metadata.name = "mynode"

    result = MagicMock()
    result.items = [node]
    v1.list_node.return_value = result

    res = MagicMock()
    res.status = "Success"
    v1.delete_node.return_value = res

    delete_nodes(label_selector="k=mynode")

    v1.delete_node.assert_called_with("mynode", ANY, grace_period_seconds=None)


@patch('chaosk8s_wix.has_local_config_file', autospec=True)
@patch('chaosk8s_wix.node.actions.client', autospec=True)
@patch('chaosk8s_wix.client')
def test_cordon_node_by_name(cl, client, has_conf):
    has_conf.return_value = False

    v1 = MagicMock()
    client.CoreV1Api.return_value = v1

    node = MagicMock()
    node.metadata.name = "mynode"

    result = MagicMock()
    result.items = [node]
    v1.list_node.return_value = result

    cordon_node(name="mynode")

    body = {
        "spec": {
            "unschedulable": True
        }
    }

    v1.patch_node.assert_called_with("mynode", body)


@patch('chaosk8s_wix.has_local_config_file', autospec=True)
@patch('chaosk8s_wix.node.actions.client', autospec=True)
@patch('chaosk8s_wix.client')
def test_uncordon_node_by_name(cl, client, has_conf):
    has_conf.return_value = False

    v1 = MagicMock()
    client.CoreV1Api.return_value = v1

    node = MagicMock()
    node.metadata.name = "mynode"

    result = MagicMock()
    result.items = [node]
    v1.list_node.return_value = result

    uncordon_node(name="mynode")

    body = {
        "spec": {
            "unschedulable": False
        }
    }

    v1.patch_node.assert_called_with("mynode", body)


@patch('chaosk8s_wix.has_local_config_file', autospec=True)
@patch('chaosk8s_wix.node.actions.client', autospec=True)
@patch('chaosk8s_wix.client')
def test_drain_nodes_by_name(cl, client, has_conf):
    has_conf.return_value = False

    v1 = MagicMock()
    client.CoreV1Api.return_value = v1

    node = MagicMock()
    node.metadata.name = "mynode"

    result = MagicMock()
    result.items = [node]
    v1.list_node.return_value = result
    
    owner = MagicMock()
    owner.controller = True
    owner.kind = "ReplicationSet"

    pod = MagicMock()
    pod.metadata.uid = "1"
    pod.metadata.name = "apod"
    pod.metadata.namespace = "default"
    pod.metadata.owner_references = [owner]

    pods = MagicMock()
    pods.items = [pod]
    v1.list_pod_for_all_namespaces.return_value = pods

    new_pod = MagicMock()
    new_pod.metadata.uid = "2"
    new_pod.metadata.name = "apod"
    new_pod.metadata.namespace = "default"

    v1.read_namespaced_pod.side_effect = [
        pod, new_pod
    ]

    drain_nodes(name="mynode")

    v1.create_namespaced_pod_eviction.assert_called_with(
        "apod", "default", body=ANY)


@patch('chaosk8s_wix.has_local_config_file', autospec=True)
@patch('chaosk8s_wix.node.actions.client', autospec=True)
@patch('chaosk8s_wix.client')
def test_daemonsets_cannot_be_drained(cl, client, has_conf):
    has_conf.return_value = False

    v1 = MagicMock()
    client.CoreV1Api.return_value = v1

    node = MagicMock()
    node.metadata.name = "mynode"

    result = MagicMock()
    result.items = [node]
    v1.list_node.return_value = result
    
    owner = MagicMock()
    owner.controller = True
    owner.kind = "DaemonSet"

    pod = MagicMock()
    pod.metadata.uid = "1"
    pod.metadata.name = "apod"
    pod.metadata.namespace = "default"
    pod.metadata.owner_references = [owner]

    pods = MagicMock()
    pods.items = [pod]
    v1.list_pod_for_all_namespaces.return_value = pods

    drain_nodes(name="mynode")

    v1.read_namespaced_pod.assert_not_called()
    v1.create_namespaced_pod_eviction.assert_not_called()


@patch('chaosk8s_wix.has_local_config_file', autospec=True)
@patch('chaosk8s_wix.node.actions.client', autospec=True)
@patch('chaosk8s_wix.client')
def test_pod_with_local_volume_cannot_be_drained(cl, client, has_conf):
    has_conf.return_value = False

    v1 = MagicMock()
    client.CoreV1Api.return_value = v1

    node = MagicMock()
    node.metadata.name = "mynode"

    result = MagicMock()
    result.items = [node]
    v1.list_node.return_value = result
    
    owner = MagicMock()
    owner.controller = True
    owner.kind = "ReplicationSet"

    pod = MagicMock()
    pod.metadata.uid = "1"
    pod.metadata.name = "apod"
    pod.metadata.namespace = "default"
    pod.metadata.owner_references = [owner]
    volume = MagicMock()
    volume.empty_dir = True
    pod.spec.volumes = [volume]

    pods = MagicMock()
    pods.items = [pod]
    v1.list_pod_for_all_namespaces.return_value = pods

    drain_nodes(name="mynode")

    v1.read_namespaced_pod.assert_not_called()
    v1.create_namespaced_pod_eviction.assert_not_called()


@patch('chaosk8s_wix.has_local_config_file', autospec=True)
@patch('chaosk8s_wix.node.actions.client', autospec=True)
@patch('chaosk8s_wix.client')
def test_pod_with_local_volume_cannot_be_drained_unless_forced(cl, client,
                                                               has_conf):
    has_conf.return_value = False

    v1 = MagicMock()
    client.CoreV1Api.return_value = v1

    node = MagicMock()
    node.metadata.name = "mynode"

    result = MagicMock()
    result.items = [node]
    v1.list_node.return_value = result
    
    owner = MagicMock()
    owner.controller = True
    owner.kind = "ReplicationSet"

    pod = MagicMock()
    pod.metadata.uid = "1"
    pod.metadata.name = "apod"
    pod.metadata.namespace = "default"
    pod.metadata.owner_references = [owner]

    pods = MagicMock()
    pods.items = [pod]
    v1.list_pod_for_all_namespaces.return_value = pods

    new_pod = MagicMock()
    new_pod.metadata.uid = "2"
    new_pod.metadata.name = "apod"
    new_pod.metadata.namespace = "default"

    v1.read_namespaced_pod.side_effect = [
        pod, new_pod
    ]

    drain_nodes(name="mynode", delete_pods_with_local_storage=True)

    v1.create_namespaced_pod_eviction.assert_called_with(
        "apod", "default", body=ANY)


@patch('chaosk8s_wix.has_local_config_file', autospec=True)
@patch('chaosk8s_wix.node.actions.client', autospec=True)
@patch('chaosk8s_wix.client')
def test_mirror_pod_cannot_be_drained(cl, client, has_conf):
    has_conf.return_value = False

    v1 = MagicMock()
    client.CoreV1Api.return_value = v1

    node = MagicMock()
    node.metadata.name = "mynode"

    result = MagicMock()
    result.items = [node]
    v1.list_node.return_value = result
    
    owner = MagicMock()
    owner.controller = True
    owner.kind = "ReplicationSet"

    pod = MagicMock()
    pod.metadata.uid = "1"
    pod.metadata.name = "apod"
    pod.metadata.namespace = "default"
    pod.metadata.owner_references = [owner]
    pod.metadata.annotations = {
        "kubernetes.io/config.mirror": "..."
    }

    pods = MagicMock()
    pods.items = [pod]
    v1.list_pod_for_all_namespaces.return_value = pods

    drain_nodes(name="mynode")

    v1.read_namespaced_pod.assert_not_called()
    v1.create_namespaced_pod_eviction.assert_not_called()


@patch('chaosk8s_wix.has_local_config_file', autospec=True)
@patch('chaosk8s_wix.node.actions.client', autospec=True)
@patch('chaosk8s_wix.client')
def test_remove_label_from_node(cl, client, has_conf):
    fake_node_name = "fake_node.com"

    has_conf.return_value = False
    v1 = MagicMock()

    condition = k8sClient.V1NodeCondition(type="Ready", status="True")
    status = k8sClient.V1NodeStatus(conditions=[condition])
    spec = k8sClient.V1NodeSpec(unschedulable=False)
    metadata = k8sClient.V1ObjectMeta(name=fake_node_name,labels={"label1": "True"})
    node = k8sClient.V1Node(status=status, spec=spec, metadata = metadata)
    response = k8sClient.V1NodeList(items=[node])

    v1.list_node_with_http_info.return_value = response
    v1.patch_node.return_value = node
    client.CoreV1Api.return_value = v1

    label_selector = 'label_default=true, label1=True'

    remove_label_from_node(label_selector, "label1")

    v1.list_node_with_http_info.assert_called_with(
        label_selector=label_selector, _preload_content=True, _return_http_data_only=True)
    v1.patch_node.assert_called_with(
        fake_node_name, {'metadata': {'labels': {'label1': None}}})

@patch('chaosk8s_wix.has_local_config_file', autospec=True)
@patch('chaosk8s_wix.node.actions.client', autospec=True)
@patch('chaosk8s_wix.client')
def test_add_label_to_node(cl, client, has_conf):
    fake_node_name = "fake_node.com"

    has_conf.return_value = False
    v1 = MagicMock()

    condition = k8sClient.V1NodeCondition(type="Ready", status="True")
    status = k8sClient.V1NodeStatus(conditions=[condition])
    spec = k8sClient.V1NodeSpec(unschedulable=False)
    metadata = k8sClient.V1ObjectMeta(name=fake_node_name,labels={"label1": "True"})
    node = k8sClient.V1Node(status=status, spec=spec, metadata = metadata)
    response = k8sClient.V1NodeList(items=[node])

    v1.list_node_with_http_info.return_value = response
    v1.patch_node.return_value = node
    client.CoreV1Api.return_value = v1

    label_selector = 'label_default=true'

    add_label_to_node(label_selector=label_selector, label_name="label1", label_value="value1")

    v1.list_node_with_http_info.assert_called_with(
        label_selector=label_selector, _preload_content=True, _return_http_data_only=True)
    v1.patch_node.assert_called_with(
        fake_node_name, {'metadata': {'labels': {'label1': "value1"}}})

@patch('chaosk8s_wix.has_local_config_file', autospec=True)
@patch('chaosk8s_wix.node.actions.client', autospec=True)
@patch('chaosk8s_wix.client')
def test_taint_node(cl, client, has_conf):
    fake_node_name = "fake_node.com"

    has_conf.return_value = False
    v1 = MagicMock()

    condition = k8sClient.V1NodeCondition(type="Ready", status="True")
    status = k8sClient.V1NodeStatus(conditions=[condition])
    spec = k8sClient.V1NodeSpec(unschedulable=False)
    metadata = k8sClient.V1ObjectMeta(name=fake_node_name,labels={"label1": "True"})
    node = k8sClient.V1Node(status=status, spec=spec, metadata = metadata)
    response = k8sClient.V1NodeList(items=[node])

    v1.list_node_with_http_info.return_value = response
    v1.patch_node.return_value = node
    client.CoreV1Api.return_value = v1

    label_selector = 'label_default=true, label1=True'

    taint_node(label_selector=label_selector, key="key1", value="Apps",  effect="NoExec")

    v1.list_node_with_http_info.assert_called_with(
        label_selector=label_selector, _preload_content=True, _return_http_data_only=True)
    v1.patch_node.assert_called_with(
        fake_node_name,  {'spec': {'taints': [{'effect': 'NoExec', 'key': 'key1', 'value': 'Apps'}]}})
