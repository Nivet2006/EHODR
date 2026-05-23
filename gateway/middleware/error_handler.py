import logging
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger("gateway")

def register_error_handlers(app: FastAPI):
    """
    Hooks global error handlers into the FastAPI instance.
    Sanitizes tracebacks and returns standardized JSON outputs.
    """
    
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        trace_id = getattr(request.state, "trace_id", "unknown")
        logger.warning(f"HTTP exception intercepted: code={exc.status_code}, detail={exc.detail}, trace_id={trace_id}")
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "detail": exc.detail,
                "trace_id": trace_id
            }
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        trace_id = getattr(request.state, "trace_id", "unknown")
        # Format Pydantic errors cleanly
        error_messages = []
        for err in exc.errors():
            field = " -> ".join(map(str, err.get("loc", [])))
            msg = err.get("msg", "Validation error")
            error_messages.append(f"Field '{field}': {msg}")
            
        logger.warning(f"Validation error: {error_messages}, trace_id={trace_id}")
        
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "detail": "Request body validation failed.",
                "errors": error_messages,
                "trace_id": trace_id
            }
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception):
        trace_id = getattr(request.state, "trace_id", "unknown")
        # Log stack trace with trace_id locally for diagnostic tracking
        logger.exception(f"Unhandled server exception occurred! trace_id={trace_id}, error={str(exc)}")
        
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "detail": "An internal server error occurred. Please contact system administrators.",
                "trace_id": trace_id
            }
        )
