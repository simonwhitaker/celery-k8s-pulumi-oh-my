"""A Kubernetes Python Pulumi program"""

from pulumi_kubernetes.apps.v1 import Deployment, DeploymentSpecArgs
from pulumi_kubernetes.core.v1 import (
    ContainerArgs,
    EnvVarArgs,
    PodSpecArgs,
    PodTemplateSpecArgs,
)
from pulumi_kubernetes.meta.v1 import LabelSelectorArgs, ObjectMetaArgs

from resources.queue import rabbit_service

web_labels = {"app": "web"}

celery_broker_url = rabbit_service.metadata.apply(
    lambda metadata: f"amqp://guest:guest@{metadata.name}:5672//"
)


worker = Deployment(
    "worker",
    spec=DeploymentSpecArgs(
        selector=LabelSelectorArgs(match_labels={"app": "worker"}),
        replicas=2,
        template=PodTemplateSpecArgs(
            metadata=ObjectMetaArgs(labels={"app": "worker"}),
            spec=PodSpecArgs(
                containers=[
                    ContainerArgs(
                        name="worker",
                        image="celery-demo",
                        image_pull_policy="Never",
                        command=[
                            "uv",
                            "run",
                            "celery",
                            "-A",
                            "tasks",
                            "worker",
                            "--loglevel=info",
                        ],
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
