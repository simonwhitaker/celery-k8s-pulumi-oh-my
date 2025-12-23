"""Prometheus and KEDA infrastructure for HPA scaling"""

import pulumi_kubernetes as k8s
import yaml

from resources.queue import rabbit_service

monitoring_namespace = k8s.core.v1.Namespace(
    "monitoring",
    metadata=k8s.meta.v1.ObjectMetaArgs(name="monitoring"),
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

prometheus = k8s.helm.v3.Release(
    "prometheus",
    k8s.helm.v3.ReleaseArgs(
        chart="prometheus",
        repository_opts=k8s.helm.v3.RepositoryOptsArgs(
            repo="https://prometheus-community.github.io/helm-charts",
        ),
        version="27.52.0",
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

keda = k8s.helm.v3.Release(
    "keda",
    k8s.helm.v3.ReleaseArgs(
        chart="keda",
        repository_opts=k8s.helm.v3.RepositoryOptsArgs(
            repo="https://kedacore.github.io/charts",
        ),
        version="2.18.3",
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
