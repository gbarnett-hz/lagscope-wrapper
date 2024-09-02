import os
import kubernetes as k
import subprocess
import uuid

from fastapi import FastAPI, Response

app = FastAPI()
k.config.load_incluster_config()
v1 = k.client.CoreV1Api()

my_namespace = os.environ["MY_NAMESPACE"]
my_release_name = os.environ["MY_RELEASE_NAME"]  # release name from helm
my_hostname = os.environ["HOSTNAME"]  # e.g., releasename-lagscope-0, etc


def _perform_latency_test(ip: str) -> float:
    file_name = f"{str(uuid.uuid4())}.out"
    subprocess.run(["/app/latency-test.sh", ip, file_name])

    with open(file_name) as f:
        output = f.readlines()
    line_with_stats = output[len(output) - 1]
    avg_start = line_with_stats.find("Average =")
    avg = line_with_stats[avg_start + len("Average =") :]
    avg = avg.replace("us", "").replace("\n", "").strip()
    avg = float(avg)

    os.remove(file_name)
    return avg


@app.get("/metrics")
async def get_metrics():
    ret = v1.list_namespaced_pod(
        my_namespace, label_selector=f"app.kubernetes.io/instance={my_release_name}"
    )

    other_pod_hostnames = {
        pod.metadata.name: pod.status.pod_ip
        for pod in ret.items
        if pod.metadata.name != my_hostname
    }

    print(other_pod_hostnames)

    data = [
        "# HELP hz_network_latency latency in us between two members",
        "# TYPE hz_network_latency gauge",
    ]

    for hostname, ip in other_pod_hostnames.items():
        if ip is None:
            continue
        print(f"Running latency test, target: {hostname} -> {ip}")
        avg = _perform_latency_test(ip)
        data.append(
            f'hz_network_latency{{src_host="{my_hostname}",dst_ip="{ip}"}} {avg}'
        )

    data.append("# EOF")
    newline_separated_data = "\n".join(data) + "\n"
    return Response(
        content=newline_separated_data,
        media_type="application/openmetrics-text; version=1.0.0; charset=utf-8",
    )
