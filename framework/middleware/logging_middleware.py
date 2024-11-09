# framework/middleware/logging_middleware.py

from framework.middleware.base_middleware import BaseMiddleware
from fastapi import Request
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseMiddleware):
    async def dispatch(self, request: Request, call_next):
        logger.info(f"Before Request: {request.method} {request.url}")
        response = await call_next(request)
        logger.info(f"After Request: {request.method} {request.url} - Status:"
                    f" {response.status_code}")
        return response
