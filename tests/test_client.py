# -*- coding: utf-8 -*-
import os
from unittest.mock import MagicMock, patch

from kubernetes import client, config
import pytest

from chaosk8s_wix import create_k8s_api_client

# Managing kube config through env vars or local configurations is complicated because it requires addtional
# integrations on local machines and on task executors in cloud
@patch('chaosk8s_wix.has_local_config_file', autospec=True)
def Xtest_client_can_be_created_from_environ(has_conf):
    has_conf.return_value = False
    os.environ.update({
        "KUBERNETES_HOST": "http://someplace",
        "KUBERNETES_API_KEY": "6789",
        "KUBERNETES_API_KEY_PREFIX": "Boom"
    })
    api = create_k8s_api_client()
    assert api.configuration.host == "http://someplace"
    assert api.configuration.api_key.get("authorization", "6789")
    assert api.configuration.api_key_prefix.get("authorization", "Boom")

# Managing kube config through env vars or local configurations is complicated because it requires addtional
# integrations on local machines and on task executors in cloud
@patch('chaosk8s_wix.has_local_config_file', autospec=True)
def Xtest_client_can_be_created_from_secrets(has_conf):
    has_conf.return_value = False
    secrets = {
        "KUBERNETES_HOST": "http://someplace",
        "KUBERNETES_API_KEY": "6789",
        "KUBERNETES_API_KEY_PREFIX": "Boom"
    }
    api = create_k8s_api_client(secrets)
    assert api.configuration.host == "http://someplace"
    assert api.configuration.api_key.get("authorization", "6789")
    assert api.configuration.api_key_prefix.get("authorization", "Boom")


@patch('chaosk8s_wix.has_local_config_file', autospec=True)
@patch('chaosk8s_wix.config.load_incluster_config', autospec=True)
def Xtest_client_can_be_created_from_secrets(load_incluster_config, has_conf):
    os.environ["CHAOSTOOLKIT_IN_POD"] = "true"

    try:
        has_conf.return_value = False
        load_incluster_config.return_value = None
        api = create_k8s_api_client()
        load_incluster_config.assert_called_once_with()
    finally:
        os.environ.pop("CHAOSTOOLKIT_IN_POD", None)


@patch('chaosk8s_wix.has_local_config_file', autospec=True)
@patch('chaosk8s_wix.config', autospec=True)
def Xtest_client_can_provide_a_context(cfg, has_conf):
    has_conf.return_value = True
    cfg.new_client_from_config = MagicMock()
    try:
        os.environ.pop("NASA_SECRETS_URL", None)
        os.environ.pop("NASA_TOKEN", None)
        os.environ.update({
            "KUBERNETES_CONTEXT": "minikube"
        })
        api = create_k8s_api_client()
        cfg.new_client_from_config.assert_called_with(context="minikube")
    finally:
        os.environ.pop("KUBERNETES_CONTEXT", None)
