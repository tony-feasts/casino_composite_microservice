# framework/middleware/correlation_id_middleware.py
import uuid
from framework.middleware.base_middleware import BaseMiddleware
from starlette.requests import Request
from opentelemetry.trace import get_current_span

class CorrelationIDMiddleware(BaseMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Check for an incoming correlation ID; if none, generate a new one
        correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
        request.state.correlation_id = correlation_id  # Store it in the request state

        # Add the correlation ID to the current OpenTelemetry span, if tracing is active
        span = get_current_span()
        if span and span.is_recording():
            span.set_attribute("correlation_id", correlation_id)

        # Process the request and add the correlation ID to the response
        response = await call_next(request)
        response.headers["X-Correlation-ID"] = correlation_id
        return response