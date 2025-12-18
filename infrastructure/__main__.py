"""A Kubernetes Python Pulumi program"""

import pulumi
from pulumi_kubernetes.apps.v1 import Deployment, DeploymentSpecArgs
from pulumi_kubernetes.core.v1 import (
    ContainerArgs,
    EnvVarArgs,
    PodSpecArgs,
    PodTemplateSpecArgs,
    Service,
    ServicePortArgs,
    ServiceSpecArgs,
)
from pulumi_kubernetes.meta.v1 import LabelSelectorArgs, ObjectMetaArgs

import resources.worker  # noqa: F401
import resources.monitoring  # noqa: F401
from resources.queue import celery_broker_url

web_labels = {"app": "web"}


web = Deployment(
    "web",
    spec=DeploymentSpecArgs(
        selector=LabelSelectorArgs(match_labels=web_labels),
        replicas=2,
        template=PodTemplateSpecArgs(
            metadata=ObjectMetaArgs(labels=web_labels),
            spec=PodSpecArgs(
                containers=[
                    ContainerArgs(
                        name="web",
                        image="celery-demo",
                        image_pull_policy="Never",
                        env=[
                            EnvVarArgs(
                                name="CELERY_BROKER_URL",
                                value=celery_broker_url,
                            ),
                        ],
                    ),
                ]
            ),
        ),
    ),
)


web_service = Service(
    "celery-demo-service",
    metadata=ObjectMetaArgs(labels=web_labels),
    spec=ServiceSpecArgs(
        selector=web_labels,
        ports=[
            ServicePortArgs(
                protocol="TCP",
                port=80,
                target_port=8000,
            )
        ],
        type="LoadBalancer",
    ),
)

pulumi.export("celery_broker_url", celery_broker_url)
