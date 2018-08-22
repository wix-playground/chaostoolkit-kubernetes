from kubernetes import client, config


def getNodes():
    config.load_kube_config()

    v1 = client.CoreV1Api()

    ret = v1.list_node_with_http_info(_preload_content=True,_return_http_data_only=True)

    print(ret)
    items_in_list = ret.items

    for item in items_in_list:
        for condition in item.status.conditions:
            if condition.type == "Ready" and condition.status == "False":
                retval = False
                break
        if item.spec.unschedulable:
            retval = False
            break


getNodes()