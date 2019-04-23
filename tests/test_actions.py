# -*- coding: utf-8 -*-
from unittest.mock import ANY, MagicMock, patch

from chaoslib.exceptions import FailedActivity
from kubernetes import client as k8sClient
from kubernetes.client.rest import ApiException
import pytest

from chaosk8s_wix.actions import start_microservice ,deploy_service_in_random_namespace
from chaosk8s_wix.node.actions import cordon_node, create_node, delete_nodes, \
    uncordon_node, drain_nodes, remove_label_from_node, taint_nodes_by_label, add_label_to_node,generate_patch_for_taint,generate_patch_for_taint_deletion
from chaosk8s_wix.aws.actions import tag_random_node_aws,attach_sq_to_instance_by_tag,iptables_block_port
from common import create_node_object ,create_config_with_taint_ignore
import os

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
@patch('chaosk8s_wix.node.client', autospec=True)
@patch('chaosk8s_wix.client')
def test_remove_label_from_node(cl, client, has_conf):
    fake_node_name = "fake_node.com"

    has_conf.return_value = False
    v1 = MagicMock()

    condition = k8sClient.V1NodeCondition(type="Ready", status="True")
    status = k8sClient.V1NodeStatus(conditions=[condition])
    spec = k8sClient.V1NodeSpec(unschedulable=False)
    metadata = k8sClient.V1ObjectMeta(name=fake_node_name, labels={"label1": "True"})
    node = k8sClient.V1Node(status=status, spec=spec, metadata=metadata)
    response = k8sClient.V1NodeList(items=[node])

    v1.list_node_with_http_info.return_value = response
    v1.patch_node.return_value = node
    client.CoreV1Api.return_value = v1
    client.V1NodeList.return_value = k8sClient.V1NodeList(items=[])

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
    metadata = k8sClient.V1ObjectMeta(name=fake_node_name, labels={"label1": "True"})
    node = k8sClient.V1Node(status=status, spec=spec, metadata=metadata)
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
def test_taint_nodes_by_label(cl, client, has_conf):
    fake_node_name = "fake_node.com"

    has_conf.return_value = False
    v1 = MagicMock()

    condition = k8sClient.V1NodeCondition(type="Ready", status="True")
    status = k8sClient.V1NodeStatus(conditions=[condition])
    spec = k8sClient.V1NodeSpec(unschedulable=False)
    metadata = k8sClient.V1ObjectMeta(name=fake_node_name, labels={"label1": "True"})
    node = k8sClient.V1Node(status=status, spec=spec, metadata=metadata)

    response = k8sClient.V1NodeList(items=[node])

    v1.list_node_with_http_info.return_value = response
    v1.patch_node.return_value = node
    client.CoreV1Api.return_value = v1
    client.V1Taint.return_value = k8sClient.V1Taint(key="", value="", effect="")


    label_selector = 'label_default=true, label1=True'

    taint_nodes_by_label(label_selector=label_selector, key="key1", value="Apps", effect="NoExec")
    v1.patch_node.assert_called()
    args = v1.patch_node.call_args[0]
    assert args[0] == fake_node_name
    assert args[1]['spec']['taints'][0].key == "key1"
    assert args[1]['spec']['taints'][0].effect == "NoExec"
    assert args[1]['spec']['taints'][0].value == "Apps"



@patch('chaosk8s_wix.aws.actions.boto3', autospec=True)
@patch('chaosk8s_wix.has_local_config_file', autospec=True)
@patch('chaosk8s_wix.node.client.CoreV1Api', autospec=True)
def test_tag_random_node_aws_fail(clientApi, has_conf,boto_client):
    has_conf.return_value = False
    v1 = MagicMock()

    node2 = create_node_object("tainted_node_ignore")
    taint = k8sClient.V1Taint(effect="NoSchedule", key="dedicated", time_added=None, value="spot")
    node2.spec.taints = [taint]

    response = k8sClient.V1NodeList(items=[node2])
    v1.list_node_with_http_info.return_value = response
    clientApi.return_value = v1

    client = MagicMock()

    boto_client.client.return_value = client

    client.describe_instances.return_value = {'Reservations':
                                                      [{'Instances': [
                                                          {'InstanceId': "id_1",
                                                           'InstanceLifecycle': 'normal',
                                                           'PrivateDnsName': 'node1'
                                                           }
                                                      ]
                                                  }]
                                             }
    config = create_config_with_taint_ignore()

    retval, nodename = tag_random_node_aws(k8s_label_selector="label_selector",
                                           secrets=None,
                                           tag_name="test_tag",
                                           configuration=config)

    assert retval == 1



@patch('chaosk8s_wix.aws.actions.boto3', autospec=True)
@patch('chaosk8s_wix.has_local_config_file', autospec=True)
@patch('chaosk8s_wix.node.client.CoreV1Api', autospec=True)
def test_tag_random_node_aws(clientApi, has_conf,boto_client):
    has_conf.return_value = False
    v1 = MagicMock()

    node1 = create_node_object("node1")

    node2 = create_node_object("tainted_node_ignore")
    taint = k8sClient.V1Taint(effect="NoSchedule", key="dedicated", time_added=None, value="spot")
    node2.spec.taints = [taint]

    response = k8sClient.V1NodeList(items=[node1, node2])
    v1.list_node_with_http_info.return_value = response
    clientApi.return_value = v1

    client = MagicMock()
    boto_client.client.return_value = client

    client.describe_instances.return_value = {'Reservations':
                                                      [{'Instances': [
                                                          {'InstanceId': "id_1",
                                                           'InstanceLifecycle': 'normal',
                                                           'PrivateDnsName': 'node1'
                                                           }
                                                      ]
                                                  }]
                                             }
    config = create_config_with_taint_ignore()

    retval, nodename = tag_random_node_aws(k8s_label_selector="label_selector",
                                           secrets=None,
                                           tag_name="test_tag",
                                           configuration=config)

    assert retval == 0
    assert nodename == "node1"
    client.create_tags.assert_called_with(Resources=['id_1'], Tags=[{'Key': 'test_tag', 'Value': 'test_tag'}])



@patch('chaosk8s_wix.aws.actions.boto3', autospec=True)
@patch('chaosk8s_wix.has_local_config_file', autospec=True)
@patch('chaosk8s_wix.node.client', autospec=True)
def test_attach_sq_to_instance_by_tag(client, has_conf,boto_client):
    has_conf.return_value = False
    v1 = MagicMock()

    taint1 = k8sClient.V1Taint(effect="NoSchedule", key="node-role.kubernetes.io/master", value=None, time_added=None)
    taint2 = k8sClient.V1Taint(effect="NoSchedule", key="dedicated", value="spot", time_added=None)

    ignore_list = [taint1, taint2]

    node1 = create_node_object("node1")

    node2 = create_node_object("tainted_node_ignore")
    taint = k8sClient.V1Taint(effect="NoSchedule", key="dedicated", time_added=None, value="spot")
    node2.spec.taints = [taint]

    response = k8sClient.V1NodeList(items=[node1, node2])
    v1.list_node_with_http_info.return_value = response
    client.CoreV1Api.return_value = v1
    client.V1NodeList.return_value = k8sClient.V1NodeList(items=[])

    client = MagicMock()
    boto_client.client.return_value = client
    boto_client.resource.return_value = client
    network_interface = MagicMock()

    instance = MagicMock()
    instance.security_groups = [
        {
            "GroupId": "some_testsgid"
        }
    ]
    instance.network_interfaces = [network_interface]


    client.instances.filter.return_value = [instance]


    client.describe_security_groups.return_value = {'SecurityGroups':
                                                    [
                                                        {
                                                            'GroupId': "i_testsgid",
                                                        }
                                                    ]
    }
    config = create_config_with_taint_ignore()
    retval = attach_sq_to_instance_by_tag(tag_name="under_chaostest",
                                          sg_name="chaos_test_sg" ,
                                          configuration=config)

    assert retval is not None
    network_interface.modify_attribute.assert_called_with(Groups=['i_testsgid'])


@patch('chaosk8s_wix.aws.actions.boto3', autospec=True)
@patch('chaosk8s_wix.has_local_config_file', autospec=True)
@patch('chaosk8s_wix.node.client', autospec=True)
@patch('chaosk8s_wix.aws.actions.api', autospec=True)
def test_iptables_block_port_no_taint_only(fabric,client, has_conf,boto_client):
    fabric_api = MagicMock()
    fabric.return_value = fabric_api

    os.environ["SSH_KEY"] = "keytext"
    os.environ["SSH_USER"] = "whatever"

    has_conf.return_value = False
    v1 = MagicMock()

    taint1 = k8sClient.V1Taint(effect="NoSchedule", key="node-role.kubernetes.io/master", value=None, time_added=None)
    taint2 = k8sClient.V1Taint(effect="NoSchedule", key="dedicated", value="spot", time_added=None)

    ignore_list = [taint1, taint2]

    node1 = create_node_object("node1")

    node2 = create_node_object("tainted_node_ignore")
    taint = k8sClient.V1Taint(effect="NoSchedule", key="dedicated", time_added=None, value="spot")
    node2.spec.taints = [taint]

    response = k8sClient.V1NodeList(items=[node1, node2])
    v1.list_node_with_http_info.return_value = response
    client.CoreV1Api.return_value = v1
    client.V1NodeList.return_value = k8sClient.V1NodeList(items=[])

    client = MagicMock()
    boto_client.client.return_value = client
    boto_client.resource.return_value = client

    instance = MagicMock()
    instance.pivate_ip_address = "test_ip"
    instance.security_groups = [
        {
            "GroupId": "some_testsgid"
        }
    ]

    client.instances.filter.return_value = [instance]

    client.describe_security_groups.return_value = {'SecurityGroups':
        [
            {
                'GroupId': "i_testsgid",
            }
        ]
    }
    config = create_config_with_taint_ignore()


    retval = iptables_block_port(tag_name="under_chaostest", port=53, protocols=["tcp"],  configuration=config)

    assert retval is not None

    text = "iptables -I PREROUTING  -t nat -p {} --dport {} -j DNAT --to-destination 0.0.0.0:1000".format("tcp", 53)

    fabric.sudo.assert_called_with(text)


@patch('chaosk8s_wix.has_local_config_file', autospec=True)
@patch('chaosk8s_wix.actions.client', autospec=True)
@patch('chaosk8s_wix.client')
def test_terminate_pods_by_name_pattern(cl, client, has_conf,tmpdir):
    has_conf.return_value = False
    ns1 = MagicMock()
    ns1.metadata = MagicMock()
    ns1.metadata.name = "namespace1"

    result = MagicMock()
    result.items = [ns1]

    v1 = MagicMock()
    v1.list_namespace.return_value = result
    client.CoreV1Api.return_value = v1
    client.AppsV1beta1Api.return_value = v1

    d = tmpdir.mkdir("subdir")
    fh = d.join("dpl.yaml")
    fh.write("FAKEDATA")

    filename = os.path.join(fh.dirname, fh.basename)

    deploy_service_in_random_namespace(spec_path=filename )
    v1.create_namespaced_deployment.assert_called_with(
        'namespace1', body='FAKEDATA')

def test_generate_patch_for_taint_added():
    taint1 = k8sClient.V1Taint(
        effect="NoSchedule", key="com.wixpress.somekey", time_added=None, value="ssr")
    taint2 = k8sClient.V1Taint(
        effect="noExecute", key="com.wixpress.somekey", time_added=None, value="dbmng")
    existing_taints = [taint1,taint2]

    new_taint = k8sClient.V1Taint(
        effect="NoSchedule", key="com.wixpress.somekey", time_added=None, value="someother")
    patch = generate_patch_for_taint(existing_taints, new_taint)
    assert len(patch['spec']['taints']) is 3


def test_generate_patch_for_taint_already_exists():
    taint1 = k8sClient.V1Taint(
        effect="NoSchedule", key="com.wixpress.somekey", time_added=None, value="ssr")
    taint2 = k8sClient.V1Taint(
        effect="noExecute", key="com.wixpress.somekey", time_added=None, value="dbmng")
    taint_new = k8sClient.V1Taint(
        effect="noExecute", key="com.wixpress.somekey", time_added=None, value="dbmng")
    existing_taints = [taint1,taint2]


    patch = generate_patch_for_taint(existing_taints, taint_new)
    assert len(patch['spec']['taints']) is 2

def test_generate_patch_for_taint_deletion():
    taint1 = k8sClient.V1Taint(
        effect="NoSchedule", key="com.wixpress.somekey", time_added=None, value="ssr")
    taint2 = k8sClient.V1Taint(
        effect="noExecute", key="com.wixpress.somekey", time_added=None, value="dbmng")
    existing_taints = [taint1,taint2]

    patch = generate_patch_for_taint_deletion(existing_taints, taint2)
    assert len(patch['spec']['taints']) is 1
