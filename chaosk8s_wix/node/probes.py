# -*- coding: utf-8 -*-
import json
from chaoslib.types import Configuration, Secrets
from kubernetes import client
from pprint import pprint

from chaosk8s_wix import create_k8s_api_client

__all__ = ["get_nodes", "all_nodes_are_ok"]


def get_nodes(label_selector: str = None, configuration: Configuration = None,
              secrets: Secrets = None):
    """
    List all Kubernetes worker nodes in your cluster. You may filter nodes
    by specifying a label selector.
    """
    api = create_k8s_api_client(secrets)

    v1 = client.CoreV1Api(api)
    if label_selector:
        ret = v1.list_node(
            label_selector=label_selector, _preload_content=False)
    else:
        ret = v1.list_node(_preload_content=False)

    return json.loads(ret.read().decode('utf-8'))


def all_nodes_are_ok(label_selector: str = None,
                     secrets: Secrets = None):
    """
    List all Kubernetes worker nodes in your cluster. You may filter nodes
    by specifying a label selector.
    """
    retval = True
    api = create_k8s_api_client(secrets)

    v1 = client.CoreV1Api(api)
    if label_selector:
        ret = v1.list_node_with_http_info(label_selector=label_selector,
                                          _preload_content=False)
    else:
        ret = v1.list_node_with_http_info(_preload_content=False)
    pprint(ret, indent=2)
    items_in_list = ret.items
    for item in items_in_list:
        for condition in item.status.conditions:
            if condition.type == "Ready" and condition.status == "False":
                retval = False
                break

    return retval
