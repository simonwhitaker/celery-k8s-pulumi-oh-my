import time

from celery_app import celery


@celery.task
def long_running_task(duration_seconds: int):
    """Simulate a long-running task."""
    time.sleep(duration_seconds)
    print(f"Task Completed after sleeping for {duration_seconds} seconds")
    return {"delay_seconds": duration_seconds, "status": "completed"}
