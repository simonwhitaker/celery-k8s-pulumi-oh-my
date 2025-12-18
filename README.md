# Getting started

## 1. Start RabbitMQ

Start the RabbitMQ broker using Docker Compose:

```bash
docker compose up -d
```

The RabbitMQ management UI will be available at http://localhost:15672 (guest/guest).

## 2. Install dependencies

```bash
uv sync
```

## 3. Start the Celery worker

In a separate terminal, run:

```bash
uv run celery -A tasks worker --loglevel=info
```

## 4. Start the FastAPI server

```bash
uv run fastapi dev main.py
```

## Testing the task

Make a PUT request to trigger a background task:

```bash
curl -X PUT http://localhost:8000/items/42
```

The request will return immediately with `{"message": "Task started"}`, and you'll see the task complete in the Celery worker terminal after 10 seconds.
