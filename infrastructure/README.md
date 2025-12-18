# Celery Demo Infrastructure

Pulumi-based Kubernetes infrastructure for a Celery application with autoscaling workers.

## Architecture

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

## Components

### Application (`__main__.py`)

- **Web deployment**: 2 replicas serving the Flask/FastAPI app
- **Web service**: LoadBalancer exposing port 80

### Queue (`resources/queue.py`)

- **RabbitMQ deployment**: Message broker with Prometheus metrics enabled
- **RabbitMQ service**: Exposes AMQP (5672), Management UI (15672), and Prometheus metrics (15692)

### Worker (`resources/worker.py`)

- **Worker deployment**: Celery workers processing tasks from RabbitMQ
- **KEDA ScaledObject**: Autoscales workers based on queue depth

### Monitoring (`resources/monitoring.py`)

- **Prometheus**: Scrapes RabbitMQ metrics
- **KEDA**: Kubernetes Event-Driven Autoscaler

## Autoscaling

Workers autoscale based on the `celery` queue depth:

| Queue Messages | Worker Replicas |
|----------------|-----------------|
| 0              | 1 (minimum)     |
| 10             | 1               |
| 50             | 5               |
| 100+           | 10 (maximum)    |

KEDA queries Prometheus every 30 seconds using:

```promql
sum(rabbitmq_queue_messages_ready{queue="celery"})
```

### Configuration

Edit `resources/worker.py` to adjust scaling parameters:

```python
worker_scaledobject = CustomResource(
    ...
    spec={
        "minReplicaCount": 1,      # Minimum workers
        "maxReplicaCount": 10,     # Maximum workers
        "triggers": [{
            "metadata": {
                "threshold": "10",  # Messages per worker
            },
        }],
    },
)
```

## Getting started

```bash
# Store Pulumi state locally, rather than in Pulumi cloud
pulumi login file://.

# Set your local k8s context. I recommend https://orbstack.dev/ for Mac users.
pulumi config set kubernetes:context orbstack
```

## Deployment

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
kubectl port-forward -n monitoring svc/prometheus-8837babe-server 9090:80
# Open http://localhost:9090
```

## Useful Commands

```bash
# Check queue depth
kubectl run curl --rm -it --restart=Never --image=curlimages/curl -- \
  curl -s "http://prometheus-8837babe-server.monitoring.svc:80/api/v1/query?query=rabbitmq_queue_messages_ready"

# View worker logs
kubectl logs -l app=worker --tail=100 -f

# Scale manually (overrides autoscaler temporarily)
kubectl scale deployment/worker-<id> --replicas=5
```
