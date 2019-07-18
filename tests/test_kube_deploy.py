# -*- coding: utf-8 -*-
from chaosk8s_wix.actions import deploy_objects_in_random_namespace
from unittest.mock import MagicMock, patch
from os import path

fixtures = 'tests/fixtures'

@patch('chaosk8s_wix.has_local_config_file', autospec=True)
@patch('chaosk8s_wix.actions.client')
def test_deploy_deployment_single(client, has_conf):
    has_conf.return_value = False

    ns1 = MagicMock()
    ns1.metadata.name = "ns1"

    result = MagicMock(items=[ns1])

    v1 = MagicMock()
    v1.list_namespace.return_value = result
    client.CoreV1Api.return_value = v1

    v1Beta1 = MagicMock()
    client.AppsV1beta1Api.return_value = v1Beta1

    configuration = {'ns_ignore_list': []}
    secrets = { 'KUBERNETES_CONTEXT': '42'}
    deploy_objects_in_random_namespace( path.join(fixtures,'deployment.json'),configuration,secrets)
    v1Beta1.create_namespaced_deployment.assert_called_once()


@patch('chaosk8s_wix.has_local_config_file', autospec=True)
@patch('chaosk8s_wix.actions.client')
def test_deploy_deployment_single_from_jinja(client, has_conf):
    has_conf.return_value = False

    ns1 = MagicMock()
    ns1.metadata.name = "ns1"

    result = MagicMock(items=[ns1])

    v1 = MagicMock()
    v1.list_namespace.return_value = result
    client.CoreV1Api.return_value = v1

    v1Beta1 = MagicMock()

    client.AppsV1beta1Api.return_value = v1Beta1

    configuration = {'ns_ignore_list': []}
    secrets = {}
    deploy_objects_in_random_namespace(path.join(fixtures,'deployment.json.jinja'),configuration,secrets)
    v1Beta1.create_namespaced_deployment.assert_called_once()


@patch('chaosk8s_wix.has_local_config_file', autospec=True)
@patch('chaosk8s_wix.actions.client')
def test_deploy_deployment_from_list(client, has_conf):

    has_conf.return_value = False

    ns1 = MagicMock()
    ns1.metadata.name = "ns1"

    result = MagicMock(items=[ns1])

    v1 = MagicMock()
    v1.list_namespace.return_value = result
    client.CoreV1Api.return_value = v1

    v1Beta1 = MagicMock()

    client.AppsV1beta1Api.return_value = v1Beta1

    configuration = {'ns_ignore_list': []}
    secrets = {}
    deploy_objects_in_random_namespace(path.join(fixtures,'deployment_list.json'),configuration,secrets)
    assert v1Beta1.create_namespaced_deployment.call_count == 2


@patch('chaosk8s_wix.has_local_config_file', autospec=True)
@patch('chaosk8s_wix.actions.client')
def test_deploy_deployment_single_from_jinja(client, has_conf):
    has_conf.return_value = False

    ns1 = MagicMock()
    ns1.metadata.name = "ns1"

    result = MagicMock(items=[ns1])

    v1 = MagicMock()
    v1.list_namespace.return_value = result
    client.CoreV1Api.return_value = v1

    configuration = {'ns_ignore_list': []}
    secrets = { 'KUBERNETES_CONTEXT': '42', 'NASA_SECRETS_URL': 'http://someserver.com/secrets'}
    deploy_objects_in_random_namespace(path.join(fixtures, 'pod.yaml'),configuration,secrets)
    assert v1.create_namespaced_pod.call_count == 1

