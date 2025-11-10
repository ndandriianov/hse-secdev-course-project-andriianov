from pydantic import BaseModel, field_validator, Field
from typing import Annotated
import re

def normalize_string(v: str) -> str:
    if v is None:
        return v
    return re.sub(r'\s+', ' ', v.strip())

NormalizedStr = Annotated[str, Field(..., min_length=1)]

class ValidatedObjectiveCreate(BaseModel):
    title: NormalizedStr
    period_name: NormalizedStr

    @field_validator('title')
    @classmethod
    def validate_title(cls, v: str) -> str:
        v = normalize_string(v)
        if len(v) < 3:
            raise ValueError("must be at least 3 characters")
        if len(v) > 200:
            raise ValueError("must not exceed 200 characters")
        return v

    @field_validator('period_name')
    @classmethod
    def validate_period_name(cls, v: str) -> str:
        v = normalize_string(v)
        if not re.match(r'^(Q[1-4]|FY) \d{4}$', v):
            raise ValueError("must be 'Q1 2025', 'Q2 2025', ..., 'Q4 2025', or 'FY 2025'")
        return v

class ValidatedKeyResultCreate(BaseModel):
    title: NormalizedStr
    metric: NormalizedStr
    target: float = Field(..., gt=0)
    progress: float = Field(..., ge=0)

    @field_validator('title')
    @classmethod
    def validate_title(cls, v: str) -> str:
        v = normalize_string(v)
        if len(v) < 3:
            raise ValueError("must be at least 3 characters")
        if len(v) > 200:
            raise ValueError("must not exceed 200 characters")
        return v

    @field_validator('metric')
    @classmethod
    def validate_metric(cls, v: str) -> str:
        v = normalize_string(v)
        if len(v) < 1:
            raise ValueError("must not be empty")
        if len(v) > 100:
            raise ValueError("must not exceed 100 characters")
        return v

    @field_validator('progress')
    @classmethod
    def validate_progress(cls, v: float, info) -> float:
        target = info.data.get('target')
        if target is not None and v > target:
            raise ValueError("must not exceed target")
        return v