# framework/middleware/delete_auth_middleware.py

from framework.middleware.base_middleware import BaseMiddleware
from fastapi import Request, HTTPException
import jwt
import logging
import os
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ALGORITHM = "HS256"

load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY")

class DeleteAuthMiddleware(BaseMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Apply logic only for DELETE requests
        if request.method == "DELETE":
            logger.info(f"DELETE Request Received: {request.method} {request.url}")

            # Get the 'auth' header
            auth = request.headers.get("auth")
            if not auth:
                raise HTTPException(status_code=401, detail="Authorization header missing")

            # Decode the JWT
            payload = jwt.decode(auth, SECRET_KEY, algorithms=[ALGORITHM])

            # Check permissions
            if "access_game_records" not in payload.get("permissions", []):
                raise HTTPException(status_code=403, detail="Permission denied")

            logger.info(f"DELETE Token Verified: {request.method} {request.url}")

        # Call the next middleware or endpoint
        response = await call_next(request)

        # Log the response for DELETE requests
        if request.method == "DELETE":
            logger.info(f"DELETE Response: {request.method} {request.url} - Status: {response.status_code}")

        return response
