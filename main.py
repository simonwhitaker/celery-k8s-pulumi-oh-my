from typing import Union

from fastapi import FastAPI

app = FastAPI()


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/items/{item_id}")
def read_item(item_id: int, q: Union[str, None] = None):
    return {"item_id": item_id, "q": q}


@app.put("/items/{item_id}")
def create_item(item_id: int):
    # TODO: run long_running_task here in the background, using celery
    long_running_task(item_id)
    return {"message": "Task started"}


def long_running_task(item_id: int):
    # Simulate a long-running task
    import time

    time.sleep(10)
    print(f"Task Completed for item_id: {item_id}")
