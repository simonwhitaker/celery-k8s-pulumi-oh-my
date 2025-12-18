import pulumi
import pulumi_kubernetes as k8s

from resources.monitoring import keda, prometheus_server_url
from resources.queue import rabbit_service

celery_broker_url = rabbit_service.metadata.apply(
    lambda metadata: f"amqp://guest:guest@{metadata.name}:5672//"
)


worker = k8s.apps.v1.Deployment(
    "worker",
    spec=k8s.apps.v1.DeploymentSpecArgs(
        selector=k8s.meta.v1.LabelSelectorArgs(match_labels={"app": "worker"}),
        replicas=1,
        template=k8s.core.v1.PodTemplateSpecArgs(
            metadata=k8s.meta.v1.ObjectMetaArgs(labels={"app": "worker"}),
            spec=k8s.core.v1.PodSpecArgs(
                termination_grace_period_seconds=300,  # 5 min for tasks to complete
                containers=[
                    k8s.core.v1.ContainerArgs(
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
                            k8s.core.v1.EnvVarArgs(
                                name="CELERY_BROKER_URL",
                                value=celery_broker_url,
                            ),
                            k8s.core.v1.EnvVarArgs(
                                name="CELERYD_PREFETCH_MULTIPLIER",
                                value="1",  # Only prefetch 1 task to minimize lost work
                            ),
                        ],
                        resources=k8s.core.v1.ResourceRequirementsArgs(
                            requests={"cpu": "100m", "memory": "128Mi"},
                            limits={"cpu": "500m", "memory": "512Mi"},
                        ),
                    ),
                ],
            ),
        ),
    ),
)

worker_scaledobject = k8s.apiextensions.CustomResource(
    "worker-scaledobject",
    api_version="keda.sh/v1alpha1",
    kind="ScaledObject",
    metadata=k8s.meta.v1.ObjectMetaArgs(
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
