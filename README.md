# Getting started

## Running with Docker (recommended)

Start everything with Docker Compose:

```bash
docker compose up --build
```

This starts RabbitMQ, the FastAPI web server, and the Celery worker.

- Web server: http://localhost:8000
- RabbitMQ management UI: http://localhost:15672 (guest/guest)

## Running locally

### 1. Start RabbitMQ

```bash
docker compose up rabbitmq -d
```

### 2. Install dependencies

```bash
uv sync
```

### 3. Start the Celery worker

In a separate terminal:

```bash
uv run celery -A tasks worker --loglevel=info
```

### 4. Start the FastAPI server

```bash
uv run fastapi dev main.py
```

## Testing the task

Make a PUT request to trigger a background task:

```bash
curl -X PUT http://localhost:8000/items/42
```

The request will return immediately with `{"message": "Task started"}`, and you'll see the task complete in the Celery worker logs after 10 seconds.
