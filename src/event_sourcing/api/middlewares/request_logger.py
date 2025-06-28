import json
import logging
from typing import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to log all incoming requests, including headers, method, and payload.
    """

    async def dispatch(
        self, request: Request, call_next: Callable
    ) -> Response:
        try:
            body = await request.json()
        except json.JSONDecodeError:
            body = None

        logger.info(
            "Incoming request",
            extra={
                "method": request.method,
                "url": str(request.url),
                "headers": dict(request.headers),
                "query_params": dict(request.query_params),
                "body": body,
            },
        )

        response: Response = await call_next(request)

        logger.info(
            "Response status",
            extra={
                "status_code": response.status_code,
                "headers": dict(response.headers),
            },
        )

        return response
