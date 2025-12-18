import pulumi_kubernetes as k8s

RABBIT_SERVICE_NAME = "rabbitmq"

_rabbit = k8s.apps.v1.Deployment(
    "rabbitmq",
    spec=k8s.apps.v1.DeploymentSpecArgs(
        selector=k8s.meta.v1.LabelSelectorArgs(match_labels={"app": "rabbitmq"}),
        replicas=1,
        template=k8s.core.v1.PodTemplateSpecArgs(
            metadata=k8s.meta.v1.ObjectMetaArgs(labels={"app": "rabbitmq"}),
            spec=k8s.core.v1.PodSpecArgs(
                containers=[
                    k8s.core.v1.ContainerArgs(
                        name="rabbitmq",
                        image="rabbitmq:3-management",
                        ports=[
                            k8s.core.v1.ContainerPortArgs(container_port=5672),
                            k8s.core.v1.ContainerPortArgs(container_port=15672),
                            k8s.core.v1.ContainerPortArgs(
                                container_port=15692, name="prometheus"
                            ),
                        ],
                        env=[
                            k8s.core.v1.EnvVarArgs(
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

rabbit_service = k8s.core.v1.Service(
    "rabbitmq-service",
    metadata=k8s.meta.v1.ObjectMetaArgs(
        name="rabbitmq",
        labels={"app": "rabbitmq"},
    ),
    spec=k8s.core.v1.ServiceSpecArgs(
        selector={"app": "rabbitmq"},
        ports=[
            k8s.core.v1.ServicePortArgs(
                protocol="TCP",
                port=5672,
                target_port=5672,
                name="rabbitmq",
            ),
            k8s.core.v1.ServicePortArgs(
                protocol="TCP",
                port=15672,
                target_port=15672,
                name="management",
            ),
            k8s.core.v1.ServicePortArgs(
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

rabbit_management_lb = k8s.core.v1.Service(
    "rabbitmq-management-lb",
    metadata=k8s.meta.v1.ObjectMetaArgs(
        name="rabbitmq-management-lb",
        labels={"app": "rabbitmq"},
    ),
    spec=k8s.core.v1.ServiceSpecArgs(
        selector={"app": "rabbitmq"},
        ports=[
            k8s.core.v1.ServicePortArgs(
                protocol="TCP",
                port=15672,
                target_port=15672,
                name="management",
            ),
        ],
        type="LoadBalancer",
    ),
)
