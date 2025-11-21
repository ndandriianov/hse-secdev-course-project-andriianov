import logging
import re
from typing import Annotated

from pydantic import BaseModel, Field, field_validator

logger = logging.getLogger("validation")
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


def normalize_string(v: str) -> str:
    if v is None:
        return v
    normalized = re.sub(r"\s+", " ", v.strip())
    logger.info(f"Normalized string: '{v}' -> '{normalized}'")
    return normalized


NormalizedStr = Annotated[str, Field(..., min_length=1)]


class ValidatedObjectiveCreate(BaseModel):
    title: NormalizedStr
    period_name: NormalizedStr

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: str) -> str:
        original = v
        v = normalize_string(v)
        if len(v) < 3:
            logger.warning(f"Title validation failed (too short): '{original}' -> '{v}'")
            raise ValueError("must be at least 3 characters")
        if len(v) > 200:
            logger.warning(f"Title validation failed (too long): '{original}' -> '{v}'")
            raise ValueError("must not exceed 200 characters")
        logger.info(f"Title validated: '{v}'")
        return v

    @field_validator("period_name")
    @classmethod
    def validate_period_name(cls, v: str) -> str:
        original = v
        v = normalize_string(v)
        if not re.match(r"^(Q[1-4]|FY) \d{4}$", v):
            logger.warning(f"Period name format invalid: '{original}' -> '{v}'")
            raise ValueError("must be 'Q1 2025', 'Q2 2025', ..., 'Q4 2025', or 'FY 2025'")
        logger.info(f"Period name validated: '{v}'")
        return v


class ValidatedKeyResultCreate(BaseModel):
    title: NormalizedStr
    metric: NormalizedStr
    target: float = Field(..., gt=0)
    progress: float = Field(..., ge=0)

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: str) -> str:
        original = v
        v = normalize_string(v)
        if len(v) < 3:
            logger.warning(f"KR title too short: '{original}' -> '{v}'")
            raise ValueError("must be at least 3 characters")
        if len(v) > 200:
            logger.warning(f"KR title too long: '{original}' -> '{v}'")
            raise ValueError("must not exceed 200 characters")
        logger.info(f"KR title validated: '{v}'")
        return v

    @field_validator("metric")
    @classmethod
    def validate_metric(cls, v: str) -> str:
        original = v
        v = normalize_string(v)
        if len(v) < 1:
            logger.warning(f"Metric empty: '{original}'")
            raise ValueError("must not be empty")
        if len(v) > 100:
            logger.warning(f"Metric too long: '{original}' -> '{v}'")
            raise ValueError("must not exceed 100 characters")
        logger.info(f"Metric validated: '{v}'")
        return v

    @field_validator("progress")
    @classmethod
    def validate_progress(cls, v: float, info) -> float:
        target = info.data.get("target")
        if target is not None and v > target:
            logger.warning(f"Progress exceeds target: {v} > {target}")
            raise ValueError("must not exceed target")
        logger.info(f"Progress validated: {v} (target: {target})")
        return v
