from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import uuid
from database.database import SessionLocal
from database.tables import AuditLog
from utils.token import get_user_from_token  

class AuditMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        user = get_user_from_token(request)
        request.state.user = user  # Save to request.state

        response = await call_next(request)

        db = SessionLocal()
        try:
            log = AuditLog(
                id=str(uuid.uuid4()),
                user_id=user.get("id") if user else None,
                role=user.get("role") if user else None,
                endpoint=str(request.url),
                method=request.method,
                status_code=str(response.status_code),
                request_data=await request.json() if request.method != "GET" else None,
                response_data={"detail": response.status_code}
            )
            db.add(log)
            db.commit()
        except Exception:
            db.rollback()
        finally:
            db.close()

        return response

