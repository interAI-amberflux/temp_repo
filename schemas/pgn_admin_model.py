from pydantic import BaseModel, EmailStr
from typing import Optional
from enum import Enum
from datetime import datetime

class Role(str, Enum):
    org_admin = "org_admin"
    process_owner = "process_owner"
    viewer = "viewer"

class OrgUserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: Role

class OrganizationCreate(BaseModel):
    name: str
    user: OrgUserCreate


class OrganizationOut(BaseModel):
    id: str
    name: str
    createdAt: datetime

    class Config:
        orm_mode = True

class OrgUserUpdateRequest(BaseModel):
    name: Optional[str]
    email: Optional[EmailStr]
    role: Optional[Role]