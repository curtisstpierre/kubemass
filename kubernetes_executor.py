import time

import click
from kubernetes import config
from kubernetes.client import Configuration
from kubernetes.client.apis import core_v1_api
from kubernetes.client.rest import ApiException
from kubernetes.stream import stream



@click.command()
@click.argument('cmd')
@click.option('--namespace', help='Namespace to look for pods')
@click.option('--name', help='Name of pod to look for')
def mass_exec(cmd, namespace, name):
    config.load_kube_config()
    c = Configuration()
    Configuration.set_default(c)
    api = core_v1_api.CoreV1Api()
    if namespace:
        ret = api.list_namespaced_pod(namespace=namespace, watch=False)
    else:
        ret = api.list_pod_for_all_namespaces(watch=False)
    for pod in ret.items:
        if pod.status.phase in ('Running') and not name or name in pod.metadata.name:
            pod_namespace, pod_name = pod.metadata.namespace, pod.metadata.name
            print(pod_namespace, pod_name)

            resp = None
            try:
                resp = api.read_namespaced_pod(name=pod_name,
                                               namespace=pod_namespace)
            except ApiException as e:
                if e.status != 404:
                    print("Unknown error: %s" % e)
                    exit(1)
            # calling exec and wait for response.
            exec_command = [cmd]
            resp = stream(api.connect_get_namespaced_pod_exec, pod_name, pod_namespace,
                          command=exec_command,
                          stderr=True, stdin=False,
                          stdout=True, tty=False)
            print("Response: " + resp)


if __name__ == '__main__':
    mass_exec()

# # Calling exec interactively.
# exec_command = ['/bin/sh']
# resp = stream(api.connect_get_namespaced_pod_exec, name, 'default',
#               command=exec_command,
#               stderr=True, stdin=True,
#               stdout=True, tty=False,
#               _preload_content=False)
# commands = [
#     "echo test1",
#     "echo \"This message goes to stderr\" >&2",
# ]
# while resp.is_open():
#     resp.update(timeout=1)
#     if resp.peek_stdout():
#         print("STDOUT: %s" % resp.read_stdout())
#     if resp.peek_stderr():
#         print("STDERR: %s" % resp.read_stderr())
#     if commands:
#         c = commands.pop(0)
#         print("Running command... %s\n" % c)
#         resp.write_stdin(c + "\n")
#     else:
#         break
#
# resp.write_stdin("date\n")
# sdate = resp.readline_stdout(timeout=3)
# print("Server date command returns: %s" % sdate)
# resp.write_stdin("whoami\n")
# user = resp.readline_stdout(timeout=3)
# print("Server user is: %s" % user)
# resp.close()
