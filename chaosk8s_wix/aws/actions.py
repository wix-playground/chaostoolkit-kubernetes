from copy import deepcopy
import random
from typing import Any, Dict, List

import boto3
from chaoslib.exceptions import FailedActivity
from chaoslib.types import Configuration, Secrets
from logzero import logger

from chaosaws import aws_client
from chaosaws.types import AWSResponse

from collections import defaultdict

__all__ = ["as_rescale_and_kill"]


def as_rescale_and_kill(label_selector: str = None, count: int = None,
                        grace_period_seconds: int = None,
                        secrets: Secrets = None):
    """
    Rescale AS group wait for rescaling complete and kill  nodes gracefully.
    Select the appropriate nodes by label.

    Nodes are not drained beforehand so we can see how cluster behaves. Nodes
    cannot be restarted, they are really deleted. Please be careful when using
    this action.

    On certain cloud providers, you also need to delete the underneath VM
    instance as well afterwards. This is the case on GCE for instance.

    If `all` is set to `True`, all nodes will be terminated.
    If `rand` is set to `True`, one random node will be terminated.
    If ̀`count` is set to a positive number, only a upto `count` nodes
    (randomly picked) will be terminated. Otherwise, the first retrieved node
    will be terminated.
    """
    api = create_k8s_api_client(secrets)

    v1 = client.CoreV1Api(api)
    ret = v1.list_node(label_selector=label_selector)

    logger.debug("Found {d} nodes labelled '{s}'".format(
        d=len(ret.items), s=label_selector))

    nodes = ret.items
    if not nodes:
        raise FailedActivity(
            "failed to find a node that matches selector {}".format(
                label_selector))

    if rand:
        nodes = [random.choice(nodes)]
        logger.debug("Picked node '{p}' to be terminated".format(
            p=nodes[0].metadata.name))
    elif count is not None:
        nodes = random.choices(nodes, k=count)
        logger.debug("Picked {c} nodes '{p}' to be terminated".format(
            c=len(nodes), p=", ".join([n.metadata.name for n in nodes])))
    elif not all:
        nodes = [nodes[0]]
        logger.debug("Picked node '{p}' to be terminated".format(
            p=nodes[0].metadata.name))
    else:
        logger.debug("Picked all nodes '{p}' to be terminated".format(
            p=", ".join([n.metadata.name for n in nodes])))

    body = client.V1DeleteOptions()
    for n in nodes:
        res = v1.delete_node(
            n.metadata.name, body, grace_period_seconds=grace_period_seconds)

        if res.status != "Success":
            logger.debug("Terminating nodes failed: {}".format(res.message))
