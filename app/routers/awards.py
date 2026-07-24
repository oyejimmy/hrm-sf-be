"""
Awards router — HR Quarterly Awards & Nominations workflow.

Endpoints:
  POST   /api/awards/nominations            – Team lead submits a nomination
  GET    /api/awards/nominations            – List nominations (HR: all; team_lead: own project)
  PUT    /api/awards/nominations/{id}       – HR evaluates / approves / rejects
  DELETE /api/awards/nominations/{id}       – HR deletes a nomination

  POST   /api/awards                        – HR grants an award
  GET    /api/awards                        – List awards (filterable by project/quarter/type)
  PUT    /api/awards/{id}                   – HR updates citation / published state
  DELETE /api/awards/{id}                   – HR removes an award

  GET    /api/awards/dashboard              – Published awards for dashboard broadcast (all roles)

  GET    /api/awards/search/global          – Global search across employees / departments / positions
"""
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..auth import get_current_user, require_role
from ..database import get_db
from ..models.award import Award, AwardNomination
from ..models.employee import Employee
from ..models.user import User
from ..models.department import Department
from ..schemas.award import (
    AwardCreate,
    AwardResponse,
    AwardUpdate,
    NominationCreate,
    NominationEvaluate,
    NominationResponse,
    SearchResult,
)

router = APIRouter(prefix="/api/awards", tags=["awards"])


# ─── helpers ─────────────────────────────────────────────────────────────────

def _enrich_nomination(nom: AwardNomination) -> dict:
    emp = nom.nominee
    user = emp.user if emp else None
    dept = emp.department.name if (emp and emp.department) else None
    nominator = nom.nominated_by
    return {
        **{c.key: getattr(nom, c.key) for c in nom.__table__.columns},
        "nominee_name": f"{user.first_name} {user.last_name}" if user else None,
        "nominee_position": emp.position if emp else None,
        "nominee_avatar": emp.avatar_url if emp else None,
        "nominee_department": dept,
        "nominated_by_name": (
            f"{nominator.first_name} {nominator.last_name}" if nominator else None
        ),
    }


def _enrich_award(award: Award) -> dict:
    emp = award.employee
    user = emp.user if emp else None
    dept = emp.department.name if (emp and emp.department) else None
    grantor = award.granted_by
    return {
        **{c.key: getattr(award, c.key) for c in award.__table__.columns},
        "employee_name": f"{user.first_name} {user.last_name}" if user else None,
        "employee_avatar": emp.avatar_url if emp else None,
        "employee_position": emp.position if emp else None,
        "employee_department": dept,
        "granted_by_name": (
            f"{grantor.first_name} {grantor.last_name}" if grantor else None
        ),
    }


# ─── Nominations ─────────────────────────────────────────────────────────────

@router.post("/nominations", response_model=NominationResponse)
def create_nomination(
    body: NominationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role not in ("admin", "hr", "team_lead"):
        raise HTTPException(status_code=403, detail="Only team leads and HR can nominate employees")

    # Verify nominee exists
    nominee = db.query(Employee).filter(Employee.id == body.nominee_id).first()
    if not nominee:
        raise HTTPException(status_code=404, detail="Employee not found")

    # Prevent duplicate nomination for the same quarter / project
    existing = (
        db.query(AwardNomination)
        .filter(
            AwardNomination.nominee_id == body.nominee_id,
            AwardNomination.project == body.project,
            AwardNomination.quarter == body.quarter,
        )
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=409,
            detail="This employee is already nominated for this project/quarter",
        )

    nom = AwardNomination(
        nominee_id=body.nominee_id,
        nominated_by_id=current_user.id,
        project=body.project,
        reason=body.reason,
        quarter=body.quarter,
        status="pending",
    )
    db.add(nom)
    db.commit()
    db.refresh(nom)
    return _enrich_nomination(nom)


@router.get("/nominations", response_model=List[NominationResponse])
def list_nominations(
    project: Optional[str] = Query(None),
    quarter: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = db.query(AwardNomination)

    # Team leads only see nominations they submitted
    if current_user.role == "team_lead":
        q = q.filter(AwardNomination.nominated_by_id == current_user.id)
    elif current_user.role not in ("admin", "hr"):
        raise HTTPException(status_code=403, detail="Not authorized")

    if project:
        q = q.filter(AwardNomination.project == project)
    if quarter:
        q = q.filter(AwardNomination.quarter == quarter)
    if status:
        q = q.filter(AwardNomination.status == status)

    nominations = q.order_by(AwardNomination.created_at.desc()).all()
    return [_enrich_nomination(n) for n in nominations]


@router.put("/nominations/{nomination_id}", response_model=NominationResponse)
def evaluate_nomination(
    nomination_id: int,
    body: NominationEvaluate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "hr"])),
):
    nom = db.query(AwardNomination).filter(AwardNomination.id == nomination_id).first()
    if not nom:
        raise HTTPException(status_code=404, detail="Nomination not found")

    nom.status = body.status
    nom.hr_notes = body.hr_notes
    nom.evaluated_by_id = current_user.id
    nom.evaluated_at = datetime.utcnow()
    db.commit()
    db.refresh(nom)
    return _enrich_nomination(nom)


@router.delete("/nominations/{nomination_id}")
def delete_nomination(
    nomination_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "hr"])),
):
    nom = db.query(AwardNomination).filter(AwardNomination.id == nomination_id).first()
    if not nom:
        raise HTTPException(status_code=404, detail="Nomination not found")
    db.delete(nom)
    db.commit()
    return {"message": "Nomination deleted"}


# ─── Awards ──────────────────────────────────────────────────────────────────

@router.get("/dashboard")
def get_dashboard_awards(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Published awards visible to everyone on the dashboard (both types, all projects)."""
    awards = (
        db.query(Award)
        .filter(Award.is_published == True)  # noqa: E712
        .order_by(Award.created_at.desc())
        .limit(20)
        .all()
    )
    return [_enrich_award(a) for a in awards]


@router.post("/", response_model=AwardResponse)
def grant_award(
    body: AwardCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "hr"])),
):
    # Validate award_type
    if body.award_type not in ("bravo", "star_performer"):
        raise HTTPException(status_code=400, detail="award_type must be 'bravo' or 'star_performer'")

    # Validate project
    valid_projects = ("smart_forum", "medlez", "phone_world")
    if body.project not in valid_projects:
        raise HTTPException(status_code=400, detail=f"project must be one of {valid_projects}")

    # Each award type is unique per project per quarter
    existing = (
        db.query(Award)
        .filter(
            Award.award_type == body.award_type,
            Award.project == body.project,
            Award.quarter == body.quarter,
        )
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"A '{body.award_type}' award for project '{body.project}' in '{body.quarter}' already exists",
        )

    award = Award(
        employee_id=body.employee_id,
        award_type=body.award_type,
        project=body.project,
        quarter=body.quarter,
        citation=body.citation,
        is_published=body.is_published,
        granted_by_id=current_user.id,
        nomination_id=body.nomination_id,
    )
    db.add(award)
    db.commit()
    db.refresh(award)

    # If linked to a nomination, mark it approved
    if body.nomination_id:
        nom = db.query(AwardNomination).filter(AwardNomination.id == body.nomination_id).first()
        if nom:
            nom.status = "approved"
            db.commit()

    return _enrich_award(award)


@router.get("/", response_model=List[AwardResponse])
def list_awards(
    project: Optional[str] = Query(None),
    quarter: Optional[str] = Query(None),
    award_type: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role not in ("admin", "hr"):
        raise HTTPException(status_code=403, detail="Not authorized")

    q = db.query(Award)
    if project:
        q = q.filter(Award.project == project)
    if quarter:
        q = q.filter(Award.quarter == quarter)
    if award_type:
        q = q.filter(Award.award_type == award_type)

    awards = q.order_by(Award.created_at.desc()).all()
    return [_enrich_award(a) for a in awards]


@router.put("/{award_id}", response_model=AwardResponse)
def update_award(
    award_id: int,
    body: AwardUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "hr"])),
):
    award = db.query(Award).filter(Award.id == award_id).first()
    if not award:
        raise HTTPException(status_code=404, detail="Award not found")

    if body.citation is not None:
        award.citation = body.citation
    if body.is_published is not None:
        award.is_published = body.is_published

    db.commit()
    db.refresh(award)
    return _enrich_award(award)


@router.delete("/{award_id}")
def delete_award(
    award_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "hr"])),
):
    award = db.query(Award).filter(Award.id == award_id).first()
    if not award:
        raise HTTPException(status_code=404, detail="Award not found")
    db.delete(award)
    db.commit()
    return {"message": "Award deleted"}


# ─── Global Search ───────────────────────────────────────────────────────────

@router.get("/search/global", response_model=List[SearchResult])
def global_search(
    query: str = Query(..., min_length=2),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Returns grouped search results across Employees, Departments, and Positions.
    Frontend groups by `category` field.
    """
    results: list[dict] = []
    q = f"%{query}%"

    # ── Employees ──
    employees = (
        db.query(Employee)
        .join(User, Employee.user_id == User.id)
        .filter(
            (User.first_name.ilike(q))
            | (User.last_name.ilike(q))
            | (User.email.ilike(q))
            | (Employee.employee_id.ilike(q))
            | (Employee.position.ilike(q))
        )
        .limit(10)
        .all()
    )
    for emp in employees:
        u = emp.user
        role_prefix = "/admin"  # fallback; frontend can override
        results.append(
            {
                "category": "Employees",
                "id": emp.id,
                "label": f"{u.first_name} {u.last_name}",
                "subtitle": f"{emp.position or ''} · {emp.department.name if emp.department else ''}".strip(" ·"),
                "avatar": emp.avatar_url,
                "route": f"{role_prefix}/employees",
            }
        )

    # ── Departments ──
    departments = (
        db.query(Department)
        .filter(Department.name.ilike(q))
        .limit(5)
        .all()
    )
    for dept in departments:
        results.append(
            {
                "category": "Departments",
                "id": dept.id,
                "label": dept.name,
                "subtitle": None,
                "avatar": None,
                "route": "/admin/employees",
            }
        )

    # ── Positions (from Employee.position string column) ──
    from sqlalchemy import distinct

    positions = (
        db.query(distinct(Employee.position))
        .filter(Employee.position.ilike(q))
        .limit(5)
        .all()
    )
    for (pos,) in positions:
        if pos:
            results.append(
                {
                    "category": "Positions",
                    "id": hash(pos) & 0x7FFFFFFF,
                    "label": pos,
                    "subtitle": None,
                    "avatar": None,
                    "route": "/admin/employees",
                }
            )

    return results
