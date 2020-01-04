from kubernetes import client as k8sClient
from unittest.mock import MagicMock
import json

__all__ = ["create_node_object", "create_pod_object","create_config_with_taint_ignore"]

def create_node_object(name: str="default", labels: {}=None)-> k8sClient.V1Node:
    condition = k8sClient.V1NodeCondition(type="Ready", status="True")
    status = k8sClient.V1NodeStatus(conditions=[condition])
    spec = k8sClient.V1NodeSpec(unschedulable=False)
    metadata = k8sClient.V1ObjectMeta(name=name, labels=labels)
    node = k8sClient.V1Node(status=status, spec=spec, metadata=metadata)
    return node


def create_pod_object(name: str="default",  imagename: str=None,labels: {}=None, state: str="running", namespace: str="default" , node_name='node1')-> k8sClient.V1Pod:
    container_state = k8sClient.V1ContainerState(running=MagicMock())
    if state == "terminated":
        container_state = k8sClient.V1ContainerState( terminated=MagicMock())

    image = k8sClient.V1ContainerImage(names=[imagename])
    container_status = k8sClient.V1ContainerStatus(state=container_state, image=image,image_id="fakeimage", name="fakename",ready="True",restart_count=0)

    condition = k8sClient.V1PodCondition(type="Ready", status=[container_status])
    status = k8sClient.V1PodStatus(conditions=[condition],container_statuses=[container_status])
    container = k8sClient.V1Container(image=image,name="fakename1")
    spec = k8sClient.V1PodSpec(containers=[container],node_name=node_name)

    metadata = k8sClient.V1ObjectMeta(name=name, labels=labels, namespace=namespace)
    node = k8sClient.V1Pod(status=status, spec=spec, metadata=metadata)
    return node


def create_instance_object(name: str="instance_default"):
    retval = ec2.instances()
    return None

def create_config_with_taint_ignore():
    retval_text = '''{
	"taints-ignore-list": [{
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
			"key": "system.wix.com/dedicated",
			"time_added": null,
			"value": "pii"
		},
		{
			"effect": "NoSchedule",
			"key": "system.wix.com/dedicated",
			"time_added": null,
			"value": "cluster-management"
		}
	]
}'''
    retval = json.loads(retval_text)
    return retval