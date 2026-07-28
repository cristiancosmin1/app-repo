import uuid

from starlette.middleware.base import BaseHTTPMiddleware


class CorrelationMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):

        run_id = request.headers.get("X-Run-ID")

        correlation_id = request.headers.get("X-Correlation-ID")

        if correlation_id is None:
            correlation_id = str(uuid.uuid4())

        request.state.run_id = run_id
        request.state.correlation_id = correlation_id

        response = await call_next(request)

        response.headers["X-Correlation-ID"] = correlation_id

        if run_id:
            response.headers["X-Run-ID"] = run_id

        return response
