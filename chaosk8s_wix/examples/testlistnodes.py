from kubernetes import client, config


def getNodes():
    config.load_kube_config()

    v1 = client.CoreV1Api()

    ret = v1.list_node_with_http_info(_preload_content=True, return_http_data_only=True)

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
    ret = v1.list_pod_for_all_namespaces(watch=False, field_selector="spec.nodeName=ip-10-43-71-169.ec2.internal")
    for i in ret.items:
        print("%s\t%s\t%s \t%s" % (i.status.pod_ip, i.metadata.namespace, i.metadata.name, i.status))


def getPods():
    config.load_kube_config()

    v1 = client.CoreV1Api()

    ret = v1.list_pod_for_all_namespaces(watch=False, field_selector="spec.nodeName=ip-10-43-71-169.ec2.internal")
    retVal = True
    for i in ret.items:
        for status in i.status.container_statuses:
            if status.state.running is None:
                print("%s\t%s\t%s \t%s is not good" % (i.status.pod_ip, i.metadata.namespace,
                                                       i.metadata.name, i.status.container_statuses[0].state))
                retVal = False
    if retVal is False:
        print("%s\tis NOT OK" % "spec.nodeName=ip-10-43-71-169.ec2.internal")
    else:
        print("%s\tis OK" % "spec.nodeName=ip-10-43-71-169.ec2.internal")


getPods()
