from datetime import date, timedelta
from typing import List, Optional

from pydantic import BaseModel
from sqlmodel import Field, Relationship, SQLModel


# USERS
class UserBase(SQLModel):
    username: str


class User(UserBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    hashed_password: str
    objectives: List["Objective"] = Relationship(back_populates="owner")


class UserCreate(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


# PERIODS
class Period(SQLModel):
    name: str
    start_date: date
    end_date: date


def default_period_templates(now: date = date.today()):
    templates: List[Period] = []
    year = now.year
    for y in (year, year + 1):
        for q in range(1, 5):
            start = date(y, 3 * (q - 1) + 1, 1)
            end = date(y, 3 * q, 1) - timedelta(days=1) if q < 4 else date(y, 12, 31)
            templates.append(Period(name=f"Q{q} {y}", start_date=start, end_date=end))
    return templates


# OBJECTIVES
class ObjectiveBase(SQLModel):
    title: str
    period_name: str


class Objective(ObjectiveBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    owner_id: int = Field(foreign_key="user.id")
    owner: Optional[User] = Relationship(back_populates="objectives")
    key_results: List["KeyResult"] = Relationship(back_populates="objective")


class ObjectiveCreate(ObjectiveBase):
    pass


class ObjectiveRead(ObjectiveBase):
    id: int
    owner_id: int


# KEY RESULTS
class KeyResultBase(SQLModel):
    title: str
    metric: str
    target: float
    progress: float = 0.0


class KeyResult(KeyResultBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    objective_id: int = Field(foreign_key="objective.id")
    objective: Optional[Objective] = Relationship(back_populates="key_results")


class KeyResultCreate(KeyResultBase):
    pass


class KeyResultRead(KeyResultBase):
    id: int
    objective_id: int
