import pulumi_kubernetes as k8s

from resources.queue import celery_broker_url

web_labels = {"app": "web"}


web = k8s.apps.v1.Deployment(
    "web",
    metadata=k8s.meta.v1.ObjectMetaArgs(labels=web_labels),
    spec=k8s.apps.v1.DeploymentSpecArgs(
        selector=k8s.meta.v1.LabelSelectorArgs(match_labels=web_labels),
        replicas=2,
        template=k8s.core.v1.PodTemplateSpecArgs(
            metadata=k8s.meta.v1.ObjectMetaArgs(labels=web_labels),
            spec=k8s.core.v1.PodSpecArgs(
                containers=[
                    k8s.core.v1.ContainerArgs(
                        name="web",
                        image="celery-demo",
                        image_pull_policy="Never",
                        env=[
                            k8s.core.v1.EnvVarArgs(
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


web_service = k8s.core.v1.Service(
    "celery-demo-service",
    metadata=k8s.meta.v1.ObjectMetaArgs(labels=web_labels),
    spec=k8s.core.v1.ServiceSpecArgs(
        selector=web_labels,
        ports=[
            k8s.core.v1.ServicePortArgs(
                protocol="TCP",
                port=80,
                target_port=8000,
            )
        ],
        type="LoadBalancer",
    ),
)
