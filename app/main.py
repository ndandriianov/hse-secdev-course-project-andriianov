from fastapi import FastAPI
from app.database import create_db_and_tables
from app.routes import router as api_router
import uvicorn

app = FastAPI(title="OKR Tracker")

@app.on_event("startup")
def on_startup():
    create_db_and_tables()

app.include_router(api_router)

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)