"""Prometheus and KEDA infrastructure for HPA scaling"""

import yaml
from pulumi_kubernetes.core.v1 import Namespace
from pulumi_kubernetes.helm.v3 import Release, ReleaseArgs, RepositoryOptsArgs
from pulumi_kubernetes.meta.v1 import ObjectMetaArgs

from resources.queue import rabbit_service

monitoring_namespace = Namespace(
    "monitoring",
    metadata=ObjectMetaArgs(name="monitoring"),
)

extra_scrape_configs = rabbit_service.metadata.name.apply(
    lambda rabbit_service_name: yaml.dump(
        [
            {
                "job_name": "rabbitmq",
                "static_configs": [
                    {
                        "targets": [
                            f"{rabbit_service_name}.default.svc:15692",
                        ],
                    }
                ],
                "metrics_path": "/metrics",
            }
        ]
    )
)

prometheus = Release(
    "prometheus",
    ReleaseArgs(
        chart="prometheus",
        repository_opts=RepositoryOptsArgs(
            repo="https://prometheus-community.github.io/helm-charts",
        ),
        namespace=monitoring_namespace.metadata.name,
        values={
            "server": {
                "persistentVolume": {"enabled": False},
            },
            "alertmanager": {"enabled": False},
            "prometheus-pushgateway": {"enabled": False},
            "kube-state-metrics": {"enabled": True},
            "extraScrapeConfigs": extra_scrape_configs,
        },
    ),
)

prometheus_server_url = prometheus.status.apply(
    lambda status: f"http://{status['name']}-server.monitoring.svc:80"
)

keda = Release(
    "keda",
    ReleaseArgs(
        chart="keda",
        repository_opts=RepositoryOptsArgs(
            repo="https://kedacore.github.io/charts",
        ),
        namespace=monitoring_namespace.metadata.name,
        values={
            "operator": {
                "replicaCount": 1,
            },
            "metricsServer": {
                "replicaCount": 1,
            },
            "crds": {
                "install": True,
            },
        },
    ),
)
