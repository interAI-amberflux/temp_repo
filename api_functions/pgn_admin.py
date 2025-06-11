from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from database.database import get_db
from database.tables import Organization, OrgUser
from schemas.pgn_admin_model import OrganizationCreate
import uuid

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
