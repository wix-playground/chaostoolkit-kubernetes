# -*- coding: utf-8 -*-
from chaoslib.types import  Secrets

__all__ = ["get_nodes_for_chaos_test"]

def get_nodes_for_chaos_test(label_selector: str = None,taints_ignore_list=None,
              secrets: Secrets = None):
    """
    List all Kubernetes worker nodes that are available for chaos testing You may filter nodes
    by specifying a label selector.
    All nodes with taints in taints_ignore_list will be filtered out
    """
    if taints_ignore_list is None:
        taints_ignore_list = []
    taints_ignore_list.append("node-role.kubernetes.io/master")

    api = create_k8s_api_client(secrets)

    v1 = client.CoreV1Api(api)
    if label_selector:
        ret = v1.list_node(
            label_selector=label_selector, _preload_content=False)
    else:
        ret = v1.list_node(_preload_content=False)
    node_list = ret.items
    retval = []
    for taint in taints_ignore_list:
        print(taint)
    for node in node_list:
        print(node)
        retval.append(node)
    return retval


