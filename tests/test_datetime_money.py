from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation

import pytest
from pydantic import BaseModel, ValidationError, field_validator


class DateTimeModel(BaseModel):
    ts: datetime

    @field_validator("ts")
    def must_have_tzinfo_and_be_utc(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("datetime must include timezone information (Z)")
        return v.astimezone(timezone.utc)


class MoneyModel(BaseModel):
    amount: Decimal
    currency: str

    @field_validator("amount", mode="before")
    def parse_amount_as_string_and_forbid_float(cls, v):
        if isinstance(v, float):
            raise ValueError("float is not allowed for money amount")
        try:
            return Decimal(str(v))
        except (InvalidOperation, TypeError):
            raise ValueError("invalid money amount")


def test_datetime_without_tz_is_rejected():
    with pytest.raises(ValidationError):
        DateTimeModel(ts=datetime(2025, 1, 1, 12, 0, 0))


def test_datetime_with_tz_is_normalized_to_utc():
    dt = datetime(2025, 1, 1, 15, 0, 0, tzinfo=timezone.utc)
    m = DateTimeModel(ts=dt)
    assert m.ts.tzinfo is not None
    assert m.ts.utcoffset() == timezone.utc.utcoffset(m.ts)
    assert m.ts == dt


def test_money_rejects_float_and_parses_string_to_decimal():
    with pytest.raises(ValidationError):
        MoneyModel(amount=12.34, currency="USD")

    m = MoneyModel(amount="12.34", currency="USD")
    assert isinstance(m.amount, Decimal)
    assert m.amount == Decimal("12.34")
