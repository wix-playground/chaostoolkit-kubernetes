# -*- coding: utf-8 -*-
import io
from unittest.mock import MagicMock, patch, ANY
import pytest
from chaosk8s_wix.consul.probes import get_good_nodes


class FakeNode(object):
    def __init__(self, dict):
        self.__dict__ = dict


def test_get_good_nodes_all_nodes_are_good():
    good_check = {'CheckID' : 'serfHealth','Status' : 'passing'}
    node1 = MagicMock()
    node1.Node = {'Checks' : [good_check]}

    node2 = node1
    node3 = node1
    nodes = [node1, node2, node3]
    result_nodes = get_good_nodes(nodes=nodes)
    assert len(result_nodes) == 3


def test_get_good_nodes_only_1():
    good_check = {'CheckID' : 'serfHealth','Status' : 'passing'}
    bad_check = {'CheckID': 'serfHealth', 'Status': 'critical'}
    node1 = MagicMock()
    node1.Node = {'Checks': [good_check]}
    node2 = MagicMock()
    node2.Node = {'Checks': [bad_check]}
    node3 = node2
    nodes = [node1, node2, node3]
    result_nodes = get_good_nodes(nodes=nodes)
    assert len(result_nodes) == 1