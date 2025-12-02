from typing import Any, Optional

from app.schemas.problem import ProblemDetails
from fastapi import Request
from fastapi.responses import JSONResponse


class ProblemException(Exception):
    def __init__(
        self,
        status_code: int,
        title: str,
        detail: Optional[str] = None,
        type: str = "about:blank",
        instance: Optional[str] = None,
        errors: Optional[dict[str, Any]] = None,
    ):
        self.status_code = status_code
        self.title = title
        self.detail = detail
        self.type = type
        self.instance = instance
        self.errors = errors


async def problem_exception_handler(request: Request, exc: ProblemException):
    problem = ProblemDetails(
        type=exc.type,
        title=exc.title,
        status=exc.status_code,
        detail=exc.detail,
        instance=exc.instance or str(request.url),
        errors=exc.errors,
    )
    return JSONResponse(
        status_code=exc.status_code,
        content=problem.model_dump(exclude_none=True),
        headers={"Content-Type": "application/problem+json"},
    )
