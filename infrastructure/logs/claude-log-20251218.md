# Claude Code Session Log - 2025-12-18

## Summary

This session involved setting up autoscaling for Celery workers in a Pulumi-based Kubernetes infrastructure project. The goal was to scale workers based on RabbitMQ queue depth.

## Key Accomplishments

### 1. Initial Setup - CPU-based HPA (Abandoned)

- First attempted using Kubernetes native HorizontalPodAutoscaler with CPU metrics
- Added resource requests/limits to worker containers

### 2. Queue-Based Autoscaling with Prometheus Adapter (Abandoned)

- Set up Prometheus to scrape RabbitMQ metrics
- Enabled RabbitMQ Prometheus plugin on port 15692
- Attempted to use prometheus-adapter to expose external metrics
- Encountered persistent issues with metrics showing `<unknown>` in HPA

### 3. KEDA Implementation (Success)

- Switched to KEDA (Kubernetes Event-Driven Autoscaler)
- Resolved APIService conflicts between prometheus-adapter and KEDA
- Successfully configured KEDA ScaledObject to query Prometheus for queue depth
- Workers scaled from 1 to 10 based on `rabbitmq_queue_messages_ready{queue="celery"}` metric

### 4. Graceful Shutdown Configuration

- Added `terminationGracePeriodSeconds=300` to give workers 5 minutes to complete tasks
- Set `CELERYD_PREFETCH_MULTIPLIER=1` to minimize lost work during scale-down

### 5. Documentation

- Created README.md explaining the architecture and autoscaling configuration

## Final Architecture

```text
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Web App   │────▶│  RabbitMQ   │◀────│   Workers   │
│ (2 replicas)│     │  (broker)   │     │ (1-10 pods) │
└─────────────┘     └─────────────┘     └─────────────┘
                           │
                           ▼
                    ┌─────────────┐
                    │ Prometheus  │
                    │  (metrics)  │
                    └─────────────┘
                           │
                           ▼
                    ┌─────────────┐
                    │    KEDA     │
                    │(autoscaler) │
                    └─────────────┘
```

## Files Modified/Created

### `resources/worker.py`

```python
"""A Kubernetes Python Pulumi program"""

import pulumi
from pulumi_kubernetes.apps.v1 import Deployment, DeploymentSpecArgs
from pulumi_kubernetes.apiextensions import CustomResource
from pulumi_kubernetes.core.v1 import (
    ContainerArgs,
    EnvVarArgs,
    PodSpecArgs,
    PodTemplateSpecArgs,
    ResourceRequirementsArgs,
)
from pulumi_kubernetes.meta.v1 import LabelSelectorArgs, ObjectMetaArgs

from resources.queue import rabbit_service
from resources.monitoring import prometheus_server_url, keda

celery_broker_url = rabbit_service.metadata.apply(
    lambda metadata: f"amqp://guest:guest@{metadata.name}:5672//"
)


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
                ]
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
```

### `resources/monitoring.py`

```python
"""Prometheus and KEDA infrastructure for HPA scaling"""

from pulumi_kubernetes.core.v1 import Namespace
from pulumi_kubernetes.helm.v3 import Release, ReleaseArgs, RepositoryOptsArgs
from pulumi_kubernetes.meta.v1 import ObjectMetaArgs

monitoring_namespace = Namespace(
    "monitoring",
    metadata=ObjectMetaArgs(name="monitoring"),
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
            "extraScrapeConfigs": """
- job_name: 'rabbitmq'
  static_configs:
    - targets: ['rabbitmq.default.svc:15692']
  metrics_path: /metrics
""",
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
```

### `resources/queue.py`

- RabbitMQ deployment with Prometheus plugin enabled
- Exposes ports 5672 (AMQP), 15672 (Management UI), 15692 (Prometheus metrics)

### `README.md`

- Documentation explaining the architecture and autoscaling configuration

## Key Learnings

1. **Prometheus Adapter Complexity**: prometheus-adapter requires careful configuration and can be difficult to debug when metrics don't appear correctly.

2. **KEDA Advantages**: KEDA is simpler for queue-based autoscaling and integrates directly with Prometheus without needing an adapter.

3. **APIService Conflicts**: When switching between prometheus-adapter and KEDA, the `external.metrics.k8s.io` APIService can cause conflicts and may need manual deletion.

4. **Graceful Shutdown**: To prevent losing work during scale-down:
   - Set `terminationGracePeriodSeconds` longer than your longest task
   - Set `CELERYD_PREFETCH_MULTIPLIER=1` to minimize prefetched tasks
   - Celery handles `SIGTERM` gracefully by default

5. **KEDA Cooldown**: KEDA has a default 5-minute cooldown (`cooldownPeriod`) before scaling to zero, and uses Kubernetes HPA `stabilizationWindowSeconds` (default 300s) for scale-down decisions.

## Useful Commands

```bash
# Deploy infrastructure
pulumi up

# Check autoscaler status
kubectl get hpa
kubectl get scaledobject

# Watch scaling in action
kubectl get hpa -w

# View RabbitMQ management UI
kubectl port-forward svc/rabbitmq 15672:15672
# Open http://localhost:15672 (guest/guest)

# View Prometheus
kubectl port-forward -n monitoring svc/prometheus-<id>-server 9090:80
# Open http://localhost:9090

# Check queue depth via Prometheus
kubectl run curl --rm -it --restart=Never --image=curlimages/curl -- \
  curl -s "http://prometheus-<id>-server.monitoring.svc:80/api/v1/query?query=rabbitmq_queue_messages_ready"

# View worker logs
kubectl logs -l app=worker --tail=100 -f
```
