import pulumi
import pulumi_kubernetes as k8s

from resources.tailscale import tailscale_operator

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
                            k8s.core.v1.ContainerPortArgs(
                                container_port=5672, name="rabbitmq"
                            ),
                            k8s.core.v1.ContainerPortArgs(
                                container_port=15672, name="management"
                            ),
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

# Expose rabbitmq and prometheus ports inside the cluster
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
                port=15692,
                target_port=15692,
                name="prometheus",
            ),
            k8s.core.v1.ServicePortArgs(
                protocol="TCP",
                port=15672,
                target_port=15672,
                name="management",
            ),
        ],
        type="ClusterIP",
    ),
)

# Ingress to access RabbitMQ management UI via tailscale
rabbit_management_ingress = k8s.networking.v1.Ingress(
    "rabbitmq-management-ingress",
    metadata=k8s.meta.v1.ObjectMetaArgs(
        name="rabbitmq-management-ingress",
    ),
    spec=k8s.networking.v1.IngressSpecArgs(
        default_backend=k8s.networking.v1.IngressBackendArgs(
            service=k8s.networking.v1.IngressServiceBackendArgs(
                name=rabbit_service.metadata.apply(lambda m: m.name or ""),
                port=k8s.networking.v1.ServiceBackendPortArgs(number=15672),
            )
        ),
        ingress_class_name="tailscale",
        tls=[
            k8s.networking.v1.IngressTLSArgs(
                hosts=["rabbitmq-mgmt"],
            )
        ],
    ),
    opts=pulumi.ResourceOptions(
        depends_on=[
            rabbit_service,
            tailscale_operator,
        ]
    ),
)

celery_broker_url = rabbit_service.metadata.apply(
    lambda metadata: f"amqp://guest:guest@{metadata.name}:5672//"
)

rabbit_management_ingress_url = rabbit_management_ingress.status.apply(
    lambda status: f"https://{status.load_balancer.ingress[0].hostname}"
    if status and status.load_balancer and status.load_balancer.ingress
    else "unknown"
)
pulumi.export("rabbitmq_management_url", rabbit_management_ingress_url)
