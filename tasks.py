import time

from celery_app import celery


@celery.task
def long_running_task(item_id: int):
    """Simulate a long-running task."""
    time.sleep(10)
    print(f"Task Completed for item_id: {item_id}")
    return {"item_id": item_id, "status": "completed"}
