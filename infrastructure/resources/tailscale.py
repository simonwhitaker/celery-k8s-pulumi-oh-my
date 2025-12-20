"""Prometheus and KEDA infrastructure for HPA scaling"""

import pulumi
from pulumi_kubernetes.helm.v3 import Release, ReleaseArgs, RepositoryOptsArgs

tailscale_config = pulumi.Config("tailscale")
client_id = tailscale_config.require("clientId")
client_secret = tailscale_config.require_secret("clientSecret")


tailscale_operator = Release(
    "tailscale-operator",
    ReleaseArgs(
        chart="tailscale-operator",
        repository_opts=RepositoryOptsArgs(
            repo="https://pkgs.tailscale.com/helmcharts",
        ),
        version="1.92.4",
        namespace="tailscale",
        create_namespace=True,
        values={
            "oauth": {
                "clientId": client_id,
                "clientSecret": client_secret,
            }
        },
    ),
)
