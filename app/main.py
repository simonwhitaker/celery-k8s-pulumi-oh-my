from fastapi import FastAPI
from tasks import long_running_task

app = FastAPI()


@app.get("/")
def read_root():
    return {"ok": True}


@app.get("/sleep-for/{time_seconds}")
def sleep_for(time_seconds: int):
    long_running_task.delay(time_seconds)  # type: ignore[attr-defined]
    return {"message": "Task started"}
