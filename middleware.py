from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import uuid
from database.database import SessionLocal
from database.tables import AuditLog
from utils.token import get_user_from_token  
from starlette.responses import JSONResponse
import json

class AuditMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Read body before it's consumed
        body_bytes = await request.body()

        # Clone the request with body for downstream handlers
        async def receive():
            return {"type": "http.request", "body": body_bytes}
        request._receive = receive

        user = get_user_from_token(request)
        request.state.user = user

        # Continue with the request
        response = await call_next(request)

        db = SessionLocal()
        try:
            try:
                request_data = json.loads(body_bytes.decode("utf-8"))
            except Exception:
                request_data = None

            response_data = {"status": response.status_code}

            log = AuditLog(
                id=str(uuid.uuid4()),
                user_id=user.get("id") if user else None,
                role=user.get("role") if user else None,
                endpoint=str(request.url),
                method=request.method,
                status_code=str(response.status_code),
                request_data=request_data,
                response_data=response_data,
            )
            db.add(log)
            db.commit()
        except Exception:
            db.rollback()
        finally:
            db.close()

        return response
