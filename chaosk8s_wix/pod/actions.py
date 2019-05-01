# -*- coding: utf-8 -*-
import random
import re

from chaoslib.types import Secrets, Configuration
from kubernetes import client
from logzero import logger
from chaosk8s_wix.slack.client import post_message
from chaosk8s_wix.slack.logger_handler import SlackHanlder

from chaosk8s_wix import create_k8s_api_client

__all__ = ["terminate_pods", "label_random_pod_in_ns",
           "remove_label_by_label_from_pod"]

slack_handler = SlackHanlder()
slack_handler.attach(logger)


def get_random_not_empy_ns(secrets: Secrets = None, k8s_label_selector: str = "", ns_ignore_list: [] = []):
    '''
    Select random namespace that not in ns_ignore_list and has at lest one deployment
    :param secrets: secrets will be injected by chaos framework
    :param ns_ignore_list: list of ns to exclude from selection
    :return:
    '''
    api = create_k8s_api_client(secrets)
    v1 = client.CoreV1Api(api)
    ret = v1.list_namespace()

    # exclude namespaces from ignore list
    selected_ns = [
        obj.metadata.name for obj in ret.items if obj.metadata.name not in ns_ignore_list]
    logger.info("ns_ignore_list {}".format(ns_ignore_list))
    target_ns = ""
    while target_ns == "":
        ns = random.choice(selected_ns)
        ret = v1.list_namespaced_pod(ns, label_selector=k8s_label_selector)
        if len(ret.items) > 1:
            target_ns = ns
            logger.info("Found ns {} with {} pods".format(
                target_ns, len(ret.items)))
            break

    return target_ns


def label_random_ns(label_name: str = "under_chaos_test", label_value: str = "True",
                    secrets: Secrets = None, configuration: Configuration = None):
    '''
    Will select random not empty namespace, filter out all namespaces in ns_ignore_list in configuration.
    It will add label with specified name and value.

    :param label_name: label name to add to deployment
    :param label_value: label value to add to deployment
    :param configuration: injected by chaos framework
    :param secrets: injected by chaos framework
    :return: True
    '''
    body = {
        "metadata": {
            "labels": {
                label_name: label_value
            }
        }
    }
    try:
        ns = get_random_not_empy_ns(
            secrets, configuration.get('ns_ignore_list', []))
        api = create_k8s_api_client(secrets)
        v1 = client.CoreV1Api(api)

        logger.warning("Label ns {} with label {}".format(ns, label_name))
        v1.patch_namespace(ns, body)
    except Exception as x:
        logger.error("Label pod failed: {}".format(x))
    return True


def remove_label_by_label_from_pod(label_selector="", configuration: Configuration = None, secrets: Secrets = None):
    '''
    Finds all deployments with specific label and removes this label
    :param configuration: injected by chaos framework
    :param secrets: injected by chaos framework
    :param label_name: label name to remove
    :param label_value: to build label selector
    :return:
    '''
    label_name = label_selector.split('=')[0]
    body = {
        "metadata": {
            "labels": {
                label_name: None
            }
        }
    }
    try:
        api = create_k8s_api_client(secrets)
        v1 = client.CoreV1Api(api)
        ret = v1.list_pod_for_all_namespaces(label_selector)
        for pod in ret.items:
            if pod.metadata.namespace not in configuration.get("ns_ignore_list", []):
                logger.warning("Remove label {} from pod: {} ".format(
                    label_name, pod.metadata.name))
                v1.patch_namespaced_pod(pod.metadata.namespace, pod, body)
    except Exception as x:
        logger.error("Remove label from pod failed: {}".format(x.body))
    return True


def terminate_pods(label_selector: str = None, name_pattern: str = None,
                   all: bool = False, rand: bool = False,
                   ns: str = "", secrets: Secrets = None, configuration: Configuration = None):
    """
    Terminate a pod gracefully. Select the appropriate pods by label and/or
    name patterns. Whenever a pattern is provided for the name, all pods
    retrieved will be filtered out if their name do not match the given
    pattern.

    If neither `label_selector` nor `name_pattern` are provided, all pods
    in the namespace will be terminated.

    If `all` is set to `True`, all matching pods will be terminated.
    If `rand` is set to `True`, one random pod will be terminated.
    Otherwise, the first retrieved pod will be terminated.
    """
    api = create_k8s_api_client(secrets)

    if ns == "":
        ns = get_random_not_empy_ns(secrets, k8s_label_selector=label_selector,
                                    ns_ignore_list=configuration.get('ns-ignore-list', []))
    logger.info("Selected '{}' for experiment".format(ns))
    v1 = client.CoreV1Api(api)
    ret = v1.list_namespaced_pod(ns, label_selector=label_selector)

    logger.debug("Found {d} pods labelled '{s}'".format(
        d=len(ret.items), s=label_selector))

    pods = []
    if name_pattern:
        pattern = re.compile(name_pattern)
        for p in ret.items:
            if pattern.match(p.metadata.name):
                pods.append(p)
                logger.debug("Pod '{p}' match pattern".format(
                    p=p.metadata.name))
    else:
        pods = ret.items

    if rand:
        pods = [random.choice(pods)]
        logger.debug("Picked pod '{p}' (rand) to be terminated".format(
            p=pods[0].metadata.name))
    elif not all:
        pods = [pods[0]]
        logger.debug("Picked pod '{p}' to be terminated".format(
            p=pods[0].metadata.name))

    body = client.V1DeleteOptions()
    for p in pods:
        logger.warning("Killing pod " + p.metadata.name)
        res = v1.delete_namespaced_pod(
            name=p.metadata.name, namespace=ns, body=body)
