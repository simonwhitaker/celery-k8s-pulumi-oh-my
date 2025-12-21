import pulumi
from pulumi_kubernetes.apiextensions import CustomResource
from pulumi_kubernetes.apps.v1 import Deployment, DeploymentSpecArgs
from pulumi_kubernetes.core.v1 import (
    ContainerArgs,
    EnvVarArgs,
    PodSpecArgs,
    PodTemplateSpecArgs,
    ResourceRequirementsArgs,
)
from pulumi_kubernetes.meta.v1 import LabelSelectorArgs, ObjectMetaArgs

from resources.monitoring import keda, prometheus_server_url
from resources.queue import celery_broker_url

worker = Deployment(
    "worker",
    spec=DeploymentSpecArgs(
        selector=LabelSelectorArgs(match_labels={"app": "worker"}),
        replicas=1,
        template=PodTemplateSpecArgs(
            metadata=ObjectMetaArgs(labels={"app": "worker"}),
            spec=PodSpecArgs(
                termination_grace_period_seconds=300,  # 5 min for tasks to complete
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
                            EnvVarArgs(
                                name="CELERYD_PREFETCH_MULTIPLIER",
                                value="1",  # Only prefetch 1 task to minimize lost work
                            ),
                        ],
                        resources=ResourceRequirementsArgs(
                            requests={"cpu": "100m", "memory": "128Mi"},
                            limits={"cpu": "500m", "memory": "512Mi"},
                        ),
                    ),
                ],
            ),
        ),
    ),
)

worker_scaledobject = CustomResource(
    "worker-scaledobject",
    api_version="keda.sh/v1alpha1",
    kind="ScaledObject",
    metadata=ObjectMetaArgs(
        name="worker-scaledobject",
    ),
    spec={
        "scaleTargetRef": {
            "name": worker.metadata.name,
        },
        "minReplicaCount": 1,
        "maxReplicaCount": 10,
        "triggers": [
            {
                "type": "prometheus",
                "metadata": {
                    "serverAddress": prometheus_server_url,
                    "metricName": "rabbitmq_queue_messages_ready",
                    "query": 'sum(rabbitmq_queue_messages_ready{queue="celery"})',
                    "threshold": "10",
                },
            },
        ],
    },
    opts=pulumi.ResourceOptions(depends_on=[keda]),
)
