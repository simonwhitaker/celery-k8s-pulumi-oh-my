"""A Kubernetes Python Pulumi program"""

from pulumi_kubernetes.apps.v1 import Deployment, DeploymentSpecArgs
from pulumi_kubernetes.core.v1 import (
    ContainerArgs,
    ContainerPortArgs,
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
        ],
        type="ClusterIP",
    ),
)

celery_broker_url = rabbit_service.metadata.apply(
    lambda metadata: f"amqp://guest:guest@{metadata.name}:5672//"
)
