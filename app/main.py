import uvicorn
from fastapi import FastAPI, HTTPException, Request

from app.database import create_db_and_tables
from app.exceptions import ProblemException, problem_exception_handler
from app.routes import router as api_router

app = FastAPI(title="OKR Tracker")
app.add_exception_handler(ProblemException, problem_exception_handler)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    raise ProblemException(
        status_code=exc.status_code,
        title=exc.detail.split(" - ")[0] if " - " in exc.detail else "Error",
        detail=exc.detail,
        type=(
            "https://api.okr.example.com/probs/unauthorized"
            if exc.status_code == 401
            else "about:blank"
        ),
        instance=str(request.url),
    )


@app.on_event("startup")
def on_startup():
    create_db_and_tables()


app.include_router(api_router)

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
