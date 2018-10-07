# -*- coding: utf-8 -*-


from chaosk8s_wix.node import node_should_be_ignored_by_taints, is_equal_V1Taint, load_taint_list_from_dict
import json
from kubernetes import client

taint_ignore_list_text = '''
              {
               "taints-ignore-list":[
                  {
                    "effect": "NoSchedule",
                    "key": "node-role.kubernetes.io/master",
                    "time_added": null,
                    "value": null
                  },
                  {
                    "effect": "NoSchedule",
                    "key": "dedicated",
                    "time_added": null,
                    "value": "spot"
                  },
                  {
                    "effect": "NoSchedule",
                    "key": "node-role.kubernetes.io/master",
                    "time_added": null,
                    "value": null
                  }
                ]
              }'''


def test_load_taint_list_from_string():
    ignore_list = json.loads(taint_ignore_list_text)
    taint_list = load_taint_list_from_dict(ignore_list["taints-ignore-list"])
    assert len(taint_list) == 3

def test_node_is_tainted_true():
    ignore_list = load_taint_list_from_dict(json.loads(taint_ignore_list_text)["taints-ignore-list"])
    taint = client.V1Taint(effect="NoSchedule", key="node-role.kubernetes.io/master", value=None, time_added=None)

    assert node_should_be_ignored_by_taints([taint], ignore_list) is True


def test_node_is_tainted_false():
    ignore_list = load_taint_list_from_dict(json.loads(taint_ignore_list_text)["taints-ignore-list"])

    taint = client.V1Taint( effect="NoSchedule", key="somekey", value=None, time_added=None)

    assert node_should_be_ignored_by_taints([taint], ignore_list) is False


def test_is_equal_v1taint_ok():
    taint1 = client.V1Taint(effect="NoSchedule", key="dedicated",value="spot")
    taint2 = client.V1Taint(effect="NoSchedule", key="dedicated", value="spot")
    assert is_equal_V1Taint(taint1, taint2) is True
