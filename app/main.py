from fastapi import FastAPI

app = FastAPI(
    title="Task Manager API",
    description="REST API for managing tasks",
    version="0.1.0",
)


@app.get("/")
async def root():
    return {"message": "Task Manager API is running!"}


@app.get("/health")
async def health_check():
    return {"status": "ok"}