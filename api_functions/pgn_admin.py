from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from database.database import get_db
from database.tables import Organization, OrgUser
from schemas.pgn_admin_model import OrganizationCreate, OrganizationOut, OrgUserUpdateRequest
import uuid
from typing import List
from utils.token import extract_user_from_token
from sqlalchemy.orm import joinedload

router = APIRouter(prefix="/pgn-admin", tags=["PGN Admin"])

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

@router.post("/create-organization")
def create_organization_with_user(payload: OrganizationCreate, db: Session = Depends(get_db)):
    # Check if organization name already exists
    if db.query(Organization).filter(Organization.name == payload.name).first():
        raise HTTPException(status_code=400, detail="Organization name already exists.")

    if db.query(OrgUser).filter(OrgUser.email == payload.user.email).first():
        raise HTTPException(status_code=400, detail="User email already exists.")

    org_id = str(uuid.uuid4())
    user_id = str(uuid.uuid4())

    hashed_password = pwd_context.hash(payload.user.password)

    organization = Organization(id=org_id, name=payload.name)

    org_user = OrgUser(
        id=user_id,
        organizationId=org_id,
        name=payload.user.name,
        email=payload.user.email,
        role=payload.user.role,
        passwordHash=hashed_password
    )

    db.add(organization)
    db.add(org_user)
    db.commit()
    db.refresh(organization)
    db.refresh(org_user)

    return {
        "organization_id": organization.id,
        "org_user_id": org_user.id,
        "message": "Organization and user created successfully."
    }


@router.get("/organizations", response_model=List[OrganizationOut])
def get_all_organizations(
    user=Depends(extract_user_from_token),
    db: Session = Depends(get_db)
):
    if user["role"] != "pgn_admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized")

    organizations = db.query(Organization).all()
    return organizations


@router.get("/organizations/{org_id}", summary="Get full organization info")
def get_organization_detail(org_id: str, db: Session = Depends(get_db), user=Depends(extract_user_from_token)):
    if user["role"] != "pgn_admin":
        raise HTTPException(status_code=403, detail="Not authorized")

    org = db.query(Organization)\
        .options(joinedload(Organization.users))\
        .filter(Organization.id == org_id)\
        .first()

    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    return {
        "id": org.id,
        "name": org.name,
        "createdAt": org.createdAt,
        "users": [
            {
                "id": user.id,
                "email": user.email,
                "name": user.name,
                "role": user.role,
                "emailVerified": user.emailVerified,
                "createdAt": user.createdAt
            }
            for user in org.users
        ]
    }


@router.put("/organizations/{org_id}/users/{user_id}", summary="Update an OrgUser under a specific Organization")
def update_org_user(
    org_id: str,
    user_id: str,
    payload: OrgUserUpdateRequest,
    db: Session = Depends(get_db),
    user=Depends(extract_user_from_token)
):
    if user["role"] != "pgn_admin":
        raise HTTPException(status_code=403, detail="Not authorized")

    org_user = (
        db.query(OrgUser)
        .filter(OrgUser.id == user_id, OrgUser.organizationId == org_id)
        .first()
    )
    if not org_user:
        raise HTTPException(status_code=404, detail="OrgUser not found in the specified organization")

    if payload.name:
        org_user.name = payload.name
    if payload.email:
        org_user.email = payload.email
    if payload.role:
        org_user.role = payload.role

    db.commit()
    db.refresh(org_user)

    return {
        "message": "OrgUser updated successfully",
        "user": {
            "id": org_user.id,
            "name": org_user.name,
            "email": org_user.email,
            "role": org_user.role
        }
    }


@router.delete("/organizations/{org_id}", summary="Delete an organization")
def delete_organization(org_id: str, db: Session = Depends(get_db), user=Depends(extract_user_from_token)):
    if user["role"] != "pgn_admin":
        raise HTTPException(status_code=403, detail="Not authorized")

    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    db.delete(org)
    db.commit()
    return {"message": f"Organization '{org.name}' and all related users deleted."}
