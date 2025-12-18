# Celery Demo

A repo for demoing some stuff:

1. Deploying to Kubernetes with Pulumi
2. Auto-scaling a celery worker deployment based on queue size

## Caveats

I use [OrbStack](https://orbstack.dev/), which has a couple of nice features:

1. It has a built-in, single-node Kubernetes cluster
2. It allows creating ingresses in the Kubernetes cluster
3. It uses local images as an image registry when deploying to Kubernetes

If you're using some other Kubernetes cluster provider, you might need to tweak some stuff.

## Getting started

```bash
brew install --cask simonwhitaker/tap/runny
runny pulumi-login
runny pulumi-up
```

(When prompted, choose to create a new stack, and call it `localhost`).

## Testing the task

Make a GET request to trigger a background task:

```bash
curl http://web.k8s.orb.local/sleep-for/30
```

The request will return immediately with `{"message": "Task started"}`, and you'll see the task complete in the Celery worker logs after the specified number of seconds.

## Running with Docker (for testing)

This can be handy if you've hacked on the app code and want to quickly test it out.

Start everything with Docker Compose:

```bash
docker compose up --build
```

This starts RabbitMQ, the FastAPI web server, and the Celery worker.

- Web server: http://localhost:8000
- RabbitMQ management UI: http://localhost:15672 (guest/guest)
