from typing import Union

from fastapi import FastAPI

from tasks import long_running_task

app = FastAPI()


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/items/{item_id}")
def read_item(item_id: int, q: Union[str, None] = None):
    return {"item_id": item_id, "q": q}


@app.put("/items/{item_id}")
def create_item(item_id: int):
    long_running_task.delay(item_id)  # type: ignore[attr-defined]
    return {"message": "Task started"}
