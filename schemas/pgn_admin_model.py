from pydantic import BaseModel, EmailStr
from enum import Enum

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
