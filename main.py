from fastapi import FastAPI
from database.database import engine
import database.tables as tables
from middleware import AuditMiddleware
from api_functions.pgn_admin import router as pgn_admin_router

app = FastAPI()
app.add_middleware(AuditMiddleware)


# Create tables automatically
# tables.Base.metadata.create_all(bind=engine) #Run this when changing tables or adding new models

# Mount routers
app.include_router(pgn_admin_router)


@app.get("/")
def read_root():
    return {"message": "API Made by D."}

