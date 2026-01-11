import pulumi
import pulumi_kubernetes as k8s

CLUSTER_NAME = "rabbitmq-cluster"

rabbit_operator = k8s.yaml.v2.ConfigFile(
    "rabbitmq-operator",
    file="https://github.com/rabbitmq/cluster-operator/releases/download/v2.18.0/cluster-operator.yml",
)

rabbit_cluster = k8s.apiextensions.CustomResource(
    "rabbitmq-cluster",
    api_version="rabbitmq.com/v1beta1",
    kind="RabbitmqCluster",
    metadata=k8s.meta.v1.ObjectMetaArgs(
        name=CLUSTER_NAME,
    ),
    spec={
        "override": {
            "statefulSet": {
                "spec": {
                    "template": {
                        "spec": {
                            "containers": [
                                {
                                    "name": "rabbitmq",
                                    "env": [
                                        {
                                            # Enable getting per-queue metrics (e.g. filtering on queue=celery)
                                            "name": "RABBITMQ_SERVER_ADDITIONAL_ERL_ARGS",
                                            "value": "-rabbitmq_prometheus return_per_object_metrics true",
                                        }
                                    ],
                                }
                            ]
                        }
                    }
                }
            }
        },
    },
    opts=pulumi.ResourceOptions(
        depends_on=[rabbit_operator],
    ),
)

# The RabbitmqCluster operator creates a secret named <cluster-name>-default-user
# containing the auto-generated credentials (username, password, host, port)
rabbit_credentials_secret_name = f"{CLUSTER_NAME}-default-user"
