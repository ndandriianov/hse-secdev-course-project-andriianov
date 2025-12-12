from typing import Any, Optional

from pydantic import BaseModel, Field


class ProblemDetails(BaseModel):
    type: str = Field(..., description="A URI reference that identifies the problem type")
    title: str = Field(..., description="A short, human-readable summary of the problem type")
    status: int = Field(..., description="The HTTP status code")
    detail: Optional[str] = Field(
        None, description="A human-readable explanation specific to this occurrence"
    )
    instance: Optional[str] = Field(
        None, description="A URI reference that identifies the specific occurrence"
    )
    errors: Optional[dict[str, Any]] = Field(None, description="Additional error details")

    class Config:
        json_schema_extra = {
            "example": {
                "type": "https://example.com/probs/validation-error",
                "title": "Validation Error",
                "status": 400,
                "detail": "Invalid input data",
                "instance": "/objectives",
                "errors": {"period_name": ["must be provided"]},
            }
        }
