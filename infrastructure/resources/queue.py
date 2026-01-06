import pulumi
import pulumi_kubernetes as k8s

rabbit_admin_username = "admin"
# TODO: get from e.g. a Pulumi secret
rabbit_admin_password = "adminpassword"

# Required secret string data shape is documented at
# https://github.com/rabbitmq/cluster-operator/tree/main/docs/examples/external-admin-secret-credentials
rabbit_admin_user = k8s.core.v1.Secret(
    "rabbitmq-admin-user",
    metadata=k8s.meta.v1.ObjectMetaArgs(
        name="rabbitmq-admin-user",
        annotations={
            "pulumi.com/waitFor": "jsonpath={.data.username}",
        },
    ),
    string_data={
        "default_user.conf": f"""default_user = {rabbit_admin_username}
default_pass = {rabbit_admin_password}
""",
        "username": rabbit_admin_username,
        "password": rabbit_admin_password,
        # Not sure what `host` value needs to be. ¯\_(ツ)_/¯
        "host": "host-goes-here",
        "port": "5672",
        "provider": "rabbitmq",
        "type": "rabbitmq",
    },
)

rabbit_operator = k8s.yaml.v2.ConfigFile(
    "rabbitmq-operator",
    file="https://github.com/rabbitmq/cluster-operator/releases/download/v2.18.0/cluster-operator.yml",
)

rabbit_cluster = k8s.apiextensions.CustomResource(
    "rabbitmq-cluster",
    api_version="rabbitmq.com/v1beta1",
    kind="RabbitmqCluster",
    metadata=k8s.meta.v1.ObjectMetaArgs(
        name="rabbitmq-cluster",
    ),
    spec={
        "secretBackend": {
            "externalSecret": {
                "name": rabbit_admin_user.metadata.name,
            }
        }
    },
    opts=pulumi.ResourceOptions(
        depends_on=[
            rabbit_operator,
            rabbit_admin_user,
        ],
    ),
)

celery_broker_url = rabbit_cluster.metadata.apply(  # type: ignore
    lambda metadata: f"amqp://{rabbit_admin_username}:{rabbit_admin_password}@{metadata['name']}:5672//"
)
