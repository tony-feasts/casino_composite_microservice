# framework/middleware/base_middleware.py

from starlette.middleware.base import BaseHTTPMiddleware
from abc import ABC, abstractmethod

class BaseMiddleware(BaseHTTPMiddleware, ABC):
    @abstractmethod
    async def dispatch(self, request, call_next):
        pass