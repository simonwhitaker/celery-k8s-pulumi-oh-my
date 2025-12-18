import os

from celery import Celery

celery = Celery(
    "celery_demo",
    broker=os.getenv("CELERY_BROKER_URL", "amqp://guest:guest@localhost:5672//"),
    backend="rpc://",
)

celery.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
)
