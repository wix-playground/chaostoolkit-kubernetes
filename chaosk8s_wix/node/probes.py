# -*- coding: utf-8 -*-
import json
from chaoslib.types import Configuration, Secrets
from kubernetes import client

from logzero import logger
from chaosk8s_wix import create_k8s_api_client
from . import get_active_nodes, load_taint_list_from_dict

__all__ = ["get_nodes", "all_nodes_are_ok"]


def get_nodes(label_selector: str = None,
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


def check_containers_for_node(client, nodename):
    """
       Helper function.
       Checks that all pods on specific container are in running state

    """
    pods = client.list_pod_for_all_namespaces(watch=False, field_selector="spec.nodeName=" + nodename)
    retval = True
    for i in pods.items:
        if i.status.container_statuses is not None:
            for status in i.status.container_statuses:
                if status.state.running is None:
                    logger.info("%s\t%s\t%s \t%s is not good" % (
                        nodename, i.metadata.namespace, i.metadata.name, i.status.container_statuses[0].state))
                    retval = False
    if not retval:
        logger.error("%s\tis NOT OK" % nodename)
    else:
        logger.info("%s\tis OK" % nodename)
    return retval


def all_nodes_are_ok(label_selector: str = None,
                     configuration: Configuration = None,
                     secrets: Secrets = None):
    print("hello sullivan")
    """
    List all Kubernetes worker nodes in your cluster. You may filter nodes
    by specifying a label selector.
    """
    retval = True
    ignore_list = []
    if configuration is not None:
        ignore_list = load_taint_list_from_dict(configuration["taints-ignore-list"])

    resp, k8s_api_v1 = get_active_nodes(label_selector, ignore_list, secrets)

    for item in resp.items:
        localresult = True
        for condition in item.status.conditions:
            if condition.type == "Ready" and condition.status == "False":
                logger.debug("{p} Ready=False  ".format(
                    p=item.metadata.name))
                localresult = False
        if item.spec.unschedulable:
            logger.debug("{p} unschedulable ' ".format(
                p=item.metadata.name))
            localresult = False

        if item.spec.taints and len(item.spec.taints) > 0:
            logger.debug("{p} Tainted node ' ".format(
                p=item.metadata.name))
            localresult = False

        if not localresult:
            logger.debug("{p} Is not healthy ' ".format(
                p=item.metadata.name))
        if localresult is False:
            retval = localresult

    return retval
