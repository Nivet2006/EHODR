import time
import uuid
import json
import sys
import logging
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

# Set up root logger format to output raw JSON strings for production log shipping
class JsonFormatter(logging.Formatter):
    """
    Format standard log records to single-line JSON representations.
    """
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "line": record.lineno
        }
        # Add custom fields if present in extra dictionaries
        if hasattr(record, "extra_fields"):
            log_data.update(record.extra_fields)
        return json.dumps(log_data)

# Bootstrap gateway logging standard output
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(JsonFormatter())
logger = logging.getLogger("gateway")
logger.handlers = [handler]
logger.setLevel(logging.INFO)
logger.propagate = False

class StructuredLoggingMiddleware(BaseHTTPMiddleware):
    """
    Structured Logging tracing middleware.
    Instruments UUID tracing and logs execution speeds.
    """
    async def dispatch(self, request: Request, call_next) -> Response:
        # Generate unique request correlation trace ID
        trace_id = str(uuid.uuid4())
        request.state.trace_id = trace_id
        
        start_time = time.perf_counter()
        
        # Log request start event
        logger.info(
            f"HTTP Request Recieved: {request.method} {request.url.path}",
            extra={"extra_fields": {
                "trace_id": trace_id,
                "method": request.method,
                "path": request.url.path,
                "client_ip": request.client.host if request.client else "unknown"
            }}
        )
        
        try:
            response: Response = await call_next(request)
            
            # Log execution latency
            duration_ms = (time.perf_counter() - start_time) * 1000.0
            response.headers["X-Trace-ID"] = trace_id
            
            logger.info(
                f"HTTP Request Completed: {request.method} {request.url.path} -> {response.status_code}",
                extra={"extra_fields": {
                    "trace_id": trace_id,
                    "status_code": response.status_code,
                    "duration_ms": round(duration_ms, 2)
                }}
            )
            return response
            
        except Exception as e:
            # Catch and trace unhandled route execution crashes
            duration_ms = (time.perf_counter() - start_time) * 1000.0
            logger.error(
                f"HTTP Request Failed: {request.method} {request.url.path} -> Exception: {str(e)}",
                extra={"extra_fields": {
                    "trace_id": trace_id,
                    "exception": str(e),
                    "duration_ms": round(duration_ms, 2)
                }}
            )
            raise e
