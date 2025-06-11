from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import uuid
import os
from jose import jwt
from passlib.context import CryptContext

from database.database import engine, get_db
import database.tables as tables
from database.tables import PGNAdmin  # Ensure this is defined in your tables
from middleware import AuditMiddleware
from api_functions.pgn_admin import router as pgn_admin_router

from pydantic import BaseModel, EmailStr

class PGNAdminAuth(BaseModel):
    email: EmailStr
    password: str


# JWT settings
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "testsecretkey")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = 60

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

app = FastAPI()
app.add_middleware(AuditMiddleware)

# Create tables automatically
tables.Base.metadata.create_all(bind=engine) #Run this when changing tables or adding new models

# Mount routers
app.include_router(pgn_admin_router)


@app.get("/")
def read_root():
    return {"message": "API Made by D."}


@app.post("/register_pgnadmin")
def register_pgnadmin(payload: PGNAdminAuth, db: Session = Depends(get_db)):
    if db.query(PGNAdmin).filter(PGNAdmin.email == payload.email).first():
        raise HTTPException(status_code=400, detail="Email already registered.")

    hashed_password = pwd_context.hash(payload.password)
    new_admin = PGNAdmin(
        id=str(uuid.uuid4()),
        email=payload.email,
        passwordHash=hashed_password,
    )
    db.add(new_admin)
    db.commit()
    db.refresh(new_admin)
    return {"message": "PGNAdmin registered successfully", "admin_id": new_admin.id}


@app.post("/login_pgnadmin")
def login_pgnadmin(payload: PGNAdminAuth, db: Session = Depends(get_db)):
    admin = db.query(PGNAdmin).filter(PGNAdmin.email == payload.email).first()
    if not admin or not pwd_context.verify(payload.password, admin.passwordHash):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token_data = {
        "user_id": admin.id,
        "role": "pgn_admin",
        "exp": datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    }
    token = jwt.encode(token_data, SECRET_KEY, algorithm=ALGORITHM)
    return {"access_token": token, "token_type": "bearer"}
