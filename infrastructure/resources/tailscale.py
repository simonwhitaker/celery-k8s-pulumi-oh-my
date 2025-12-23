import pulumi
import pulumi_kubernetes as k8s

tailscale_config = pulumi.Config("tailscale")
client_id = tailscale_config.require("clientId")
client_secret = tailscale_config.require_secret("clientSecret")

tailscale_namespace = k8s.core.v1.Namespace(
    "tailscale-namespace",
    metadata=k8s.meta.v1.ObjectMetaArgs(name="tailscale"),
)

tailscale_operator = k8s.helm.v3.Release(
    "tailscale-operator",
    k8s.helm.v3.ReleaseArgs(
        chart="tailscale-operator",
        repository_opts=k8s.helm.v3.RepositoryOptsArgs(
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
