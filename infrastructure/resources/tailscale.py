import pulumi
from pulumi_kubernetes.core.v1 import Namespace
from pulumi_kubernetes.helm.v3 import Release, ReleaseArgs, RepositoryOptsArgs
from pulumi_kubernetes.meta.v1 import ObjectMetaArgs

tailscale_config = pulumi.Config("tailscale")
client_id = tailscale_config.require("clientId")
client_secret = tailscale_config.require_secret("clientSecret")

tailscale_namespace = Namespace(
    "tailscale-namespace",
    metadata=ObjectMetaArgs(name="tailscale"),
)

tailscale_operator = Release(
    "tailscale-operator",
    ReleaseArgs(
        chart="tailscale-operator",
        repository_opts=RepositoryOptsArgs(
            repo="https://pkgs.tailscale.com/helmcharts",
        ),
        version="1.92.4",
        namespace=tailscale_namespace.metadata.name,
        values={
            "oauth": {
                "clientId": client_id,
                "clientSecret": client_secret,
            }
        },
    ),
)
