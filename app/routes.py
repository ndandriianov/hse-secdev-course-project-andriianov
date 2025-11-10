# app/routes.py
import csv
import io
from typing import List

from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session, select

from app.auth import authenticate_user, create_access_token, get_current_user, get_password_hash
from app.database import get_session
from app.exceptions import ProblemException
from app.models import (
    KeyResult,
    KeyResultRead,
    Objective,
    ObjectiveRead,
    Period,
    Token,
    User,
    UserCreate,
    default_period_templates,
)
from app.schemas.validation import ValidatedObjectiveCreate, ValidatedKeyResultCreate

router = APIRouter()

PROBLEM_TYPES = {
    "username_exists": "https://api.okr.example.com/probs/username-exists",
    "invalid_credentials": "https://api.okr.example.com/probs/invalid-credentials",
    "validation_error": "https://api.okr.example.com/probs/validation-error",
    "resource_not_found": "https://api.okr.example.com/probs/resource-not-found",
    "access_denied": "https://api.okr.example.com/probs/access-denied",
    "duplicate_objective": "https://api.okr.example.com/probs/duplicate-objective",
    "unauthorized": "https://api.okr.example.com/probs/unauthorized",
}


# AUTH endpoints
@router.post("/signup", response_model=Token)
def signup(user_in: UserCreate, session: Session = Depends(get_session)):
    if session.exec(select(User).where(User.username == user_in.username)).first():
        raise ProblemException(
            status_code=400,
            title="Bad Request",
            detail="Username already registered",
            type=PROBLEM_TYPES["username_exists"],
        )
    user = User(username=user_in.username, hashed_password=get_password_hash(user_in.password))
    session.add(user)
    session.commit()
    session.refresh(user)
    access_token = create_access_token({"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/token", response_model=Token)
def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: Session = Depends(get_session),
):
    user = authenticate_user(session, form_data.username, form_data.password)
    if not user:
        raise ProblemException(
            status_code=400,
            title="Bad Request",
            detail="Incorrect username or password",
            type=PROBLEM_TYPES["invalid_credentials"],
        )
    access_token = create_access_token({"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}


# Period templates endpoint
@router.get("/period-templates", response_model=List[Period])
def list_period_templates():
    return default_period_templates()


# Objective CRUD
@router.post("/objectives", response_model=ObjectiveRead)
def create_objective(
    obj_in: ValidatedObjectiveCreate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    statement = select(Objective).where(
        Objective.owner_id == current_user.id,
        Objective.period_name == obj_in.period_name,
    )
    existing = session.exec(statement).first()
    if existing:
        raise ProblemException(
            status_code=400,
            title="Bad Request",
            detail="Objective in the same period already exists",
            type=PROBLEM_TYPES["duplicate_objective"],
        )
    obj = Objective(title=obj_in.title, period_name=obj_in.period_name, owner_id=current_user.id)
    session.add(obj)
    session.commit()
    session.refresh(obj)
    return ObjectiveRead(
        id=obj.id, title=obj.title, period_name=obj.period_name, owner_id=obj.owner_id
    )


@router.get("/objectives", response_model=List[ObjectiveRead])
def list_objectives(
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    objs = session.exec(
        select(Objective).where(Objective.owner_id == current_user.id).offset(skip).limit(limit)
    ).all()
    return [
        ObjectiveRead(id=o.id, title=o.title, period_name=o.period_name, owner_id=o.owner_id)
        for o in objs
    ]


@router.get("/objectives/{objective_id}", response_model=ObjectiveRead)
def get_objective(
    objective_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    obj = session.get(Objective, objective_id)
    if not obj or obj.owner_id != current_user.id:
        raise ProblemException(
            status_code=404,
            title="Not Found",
            detail="Objective not found",
            type=PROBLEM_TYPES["resource_not_found"],
            instance=f"/objectives/{objective_id}",
        )
    return ObjectiveRead(
        id=obj.id, title=obj.title, period_name=obj.period_name, owner_id=obj.owner_id
    )


@router.put("/objectives/{objective_id}", response_model=ObjectiveRead)
def update_objective(
    objective_id: int,
    obj_in: ValidatedObjectiveCreate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    obj = session.get(Objective, objective_id)
    if not obj or obj.owner_id != current_user.id:
        raise ProblemException(
            status_code=404,
            title="Not Found",
            detail="Objective not found",
            type=PROBLEM_TYPES["resource_not_found"],
            instance=f"/objectives/{objective_id}",
        )
    obj.title = obj_in.title
    obj.period_name = obj_in.period_name
    session.add(obj)
    session.commit()
    session.refresh(obj)
    return ObjectiveRead(
        id=obj.id, title=obj.title, period_name=obj.period_name, owner_id=obj.owner_id
    )


@router.delete("/objectives/{objective_id}")
def delete_objective(
    objective_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    obj = session.get(Objective, objective_id)
    if not obj or obj.owner_id != current_user.id:
        raise ProblemException(
            status_code=404,
            title="Not Found",
            detail="Objective not found",
            type=PROBLEM_TYPES["resource_not_found"],
            instance=f"/objectives/{objective_id}",
        )
    session.delete(obj)
    session.commit()
    return {"ok": True}


# KeyResult CRUD
@router.post("/objectives/{objective_id}/key-results", response_model=KeyResultRead)
def create_key_result(
    objective_id: int,
    kr_in: ValidatedKeyResultCreate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    obj = session.get(Objective, objective_id)
    if not obj or obj.owner_id != current_user.id:
        raise ProblemException(
            status_code=404,
            title="Not Found",
            detail="Objective not found or access denied",
            type=PROBLEM_TYPES["resource_not_found"],
            instance=f"/objectives/{objective_id}",
        )
    kr = KeyResult(
        title=kr_in.title,
        metric=kr_in.metric,
        target=kr_in.target,
        progress=kr_in.progress,
        objective_id=objective_id,
    )
    session.add(kr)
    session.commit()
    session.refresh(kr)
    return KeyResultRead(
        id=kr.id,
        title=kr.title,
        metric=kr.metric,
        target=kr.target,
        progress=kr.progress,
        objective_id=kr.objective_id,
    )


@router.get("/objectives/{objective_id}/key-results", response_model=List[KeyResultRead])
def list_key_results(
    objective_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    obj = session.get(Objective, objective_id)
    if not obj or obj.owner_id != current_user.id:
        raise ProblemException(
            status_code=404,
            title="Not Found",
            detail="Objective not found or access denied",
            type=PROBLEM_TYPES["resource_not_found"],
            instance=f"/objectives/{objective_id}/key-results",
        )
    results = session.exec(select(KeyResult).where(KeyResult.objective_id == objective_id)).all()
    return [
        KeyResultRead(
            id=r.id,
            title=r.title,
            metric=r.metric,
            target=r.target,
            progress=r.progress,
            objective_id=r.objective_id,
        )
        for r in results
    ]


@router.put("/key-results/{kr_id}", response_model=KeyResultRead)
def update_key_result(
    kr_id: int,
    kr_in: ValidatedKeyResultCreate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    kr = session.get(KeyResult, kr_id)
    if not kr:
        raise ProblemException(
            status_code=404,
            title="Not Found",
            detail="KeyResult not found",
            type=PROBLEM_TYPES["resource_not_found"],
            instance=f"/key-results/{kr_id}",
        )
    obj = session.get(Objective, kr.objective_id)
    if not obj or obj.owner_id != current_user.id:
        raise ProblemException(
            status_code=404,
            title="Not Found",
            detail="Objective not found or access denied",
            type=PROBLEM_TYPES["access_denied"],
            instance=f"/key-results/{kr_id}",
        )
    kr.title = kr_in.title
    kr.metric = kr_in.metric
    kr.target = kr_in.target
    kr.progress = kr_in.progress
    session.add(kr)
    session.commit()
    session.refresh(kr)
    return KeyResultRead(
        id=kr.id,
        title=kr.title,
        metric=kr.metric,
        target=kr.target,
        progress=kr.progress,
        objective_id=kr.objective_id,
    )


@router.delete("/key-results/{kr_id}")
def delete_key_result(
    kr_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    kr = session.get(KeyResult, kr_id)
    if not kr:
        raise ProblemException(
            status_code=404,
            title="Not Found",
            detail="KeyResult not found",
            type=PROBLEM_TYPES["resource_not_found"],
            instance=f"/key-results/{kr_id}",
        )
    obj = session.get(Objective, kr.objective_id)
    if not obj or obj.owner_id == current_user.id:
        raise ProblemException(
            status_code=404,
            title="Not Found",
            detail="Objective not found or access denied",
            type=PROBLEM_TYPES["access_denied"],
            instance=f"/key-results/{kr_id}",
        )
    session.delete(kr)
    session.commit()
    return {"ok": True}


# Stats endpoint
@router.get("/stats")
def get_stats(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    objs = session.exec(select(Objective).where(Objective.owner_id == current_user.id)).all()
    resp = {"objectives": []}
    total_weighted = 0.0
    total_targets = 0.0
    for o in objs:
        krs = session.exec(select(KeyResult).where(KeyResult.objective_id == o.id)).all()
        if not krs:
            obj_progress = None
        else:
            ratios = []
            for k in krs:
                ratio = k.progress / k.target if k.target > 0 else 0.0
                ratios.append(min(max(ratio, 0.0), 1.0))
            obj_progress = sum(ratios) / len(ratios)
            total_weighted += obj_progress * len(ratios)
            total_targets += len(ratios)
        resp["objectives"].append(
            {
                "id": o.id,
                "title": o.title,
                "period_name": o.period_name,
                "progress": obj_progress,
            }
        )
    overall = total_weighted / total_targets if total_targets > 0 else None
    resp["overall_progress"] = overall
    return resp


# Reports
@router.get("/reports/objective/{objective_id}")
def objective_report(
    objective_id: int,
    format: str = Query("csv", enum=["csv", "json"]),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    obj = session.get(Objective, objective_id)
    if not obj or obj.owner_id != current_user.id:
        raise ProblemException(
            status_code=404,
            title="Not Found",
            detail="Objective not found or access denied",
            type=PROBLEM_TYPES["resource_not_found"],
            instance=f"/reports/objective/{objective_id}",
        )
    krs = session.exec(select(KeyResult).where(KeyResult.objective_id == objective_id)).all()
    rows = [
        {
            "id": k.id,
            "title": k.title,
            "metric": k.metric,
            "target": k.target,
            "progress": k.progress,
        }
        for k in krs
    ]
    if format == "json":
        return {
            "objective": {
                "id": obj.id,
                "title": obj.title,
                "period_name": obj.period_name,
            },
            "key_results": rows,
        }
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=["id", "title", "metric", "target", "progress"])
    writer.writeheader()
    for r in rows:
        writer.writerow(r)
    return Response(content=output.getvalue(), media_type="text/csv")


# Health check
@router.get("/health")
def health():
    return {"status": "ok"}