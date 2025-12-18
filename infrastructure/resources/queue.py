"""A Kubernetes Python Pulumi program"""

from pulumi_kubernetes.apps.v1 import Deployment, DeploymentSpecArgs
from pulumi_kubernetes.core.v1 import (
    ContainerArgs,
    ContainerPortArgs,
    EnvVarArgs,
    PodSpecArgs,
    PodTemplateSpecArgs,
    Service,
    ServicePortArgs,
    ServiceSpecArgs,
)
from pulumi_kubernetes.meta.v1 import LabelSelectorArgs, ObjectMetaArgs

RABBIT_SERVICE_NAME = "rabbitmq"

_rabbit = Deployment(
    "rabbitmq",
    spec=DeploymentSpecArgs(
        selector=LabelSelectorArgs(match_labels={"app": "rabbitmq"}),
        replicas=1,
        template=PodTemplateSpecArgs(
            metadata=ObjectMetaArgs(labels={"app": "rabbitmq"}),
            spec=PodSpecArgs(
                containers=[
                    ContainerArgs(
                        name="rabbitmq",
                        image="rabbitmq:3-management",
                        ports=[
                            ContainerPortArgs(container_port=5672),
                            ContainerPortArgs(container_port=15672),
                            ContainerPortArgs(container_port=15692, name="prometheus"),
                        ],
                        env=[
                            EnvVarArgs(
                                name="RABBITMQ_SERVER_ADDITIONAL_ERL_ARGS",
                                value="-rabbitmq_prometheus return_per_object_metrics true",
                            ),
                        ],
                        command=["bash", "-c"],
                        args=[
                            "rabbitmq-plugins enable rabbitmq_prometheus && "
                            "exec docker-entrypoint.sh rabbitmq-server"
                        ],
                    ),
                ]
            ),
        ),
    ),
)

rabbit_service = Service(
    "rabbitmq-service",
    metadata=ObjectMetaArgs(
        name="rabbitmq",
        labels={"app": "rabbitmq"},
    ),
    spec=ServiceSpecArgs(
        selector={"app": "rabbitmq"},
        ports=[
            ServicePortArgs(
                protocol="TCP",
                port=5672,
                target_port=5672,
                name="rabbitmq",
            ),
            ServicePortArgs(
                protocol="TCP",
                port=15672,
                target_port=15672,
                name="management",
            ),
            ServicePortArgs(
                protocol="TCP",
                port=15692,
                target_port=15692,
                name="prometheus",
            ),
        ],
        type="ClusterIP",
    ),
)

celery_broker_url = rabbit_service.metadata.apply(
    lambda metadata: f"amqp://guest:guest@{metadata.name}:5672//"
)
