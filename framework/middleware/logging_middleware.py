import time
import logging
from google.cloud import logging as gcp_logging
from framework.middleware.base_middleware import BaseMiddleware
from starlette.requests import Request

# Set up Google Cloud Logging
gcp_client = gcp_logging.Client()
gcp_client.setup_logging()  # Automatically sends logs to GCP

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        correlation_id = getattr(request.state, "correlation_id",
                                 "N/A")  # Get the correlation ID

        # Log the incoming request
        logger.info(
            f"REQUEST: {request.method} {request.url} CID={correlation_id}")

        try:
            response = await call_next(request)
        except Exception as e:
            # Log any exceptions
            logger.error(
                f"ERROR: {request.method} {request.url} CID={correlation_id} Error: {e}")
            raise

        # Log the outgoing response
        duration = time.time() - start_time
        logger.info(f"RESPONSE: {request.method} {request.url} "
                    f"Status={response.status_code} Duration={duration:.2f}s CID={correlation_id}")
        return response
