"""
Global exception handling.
Intercepts HTTP and unexpected errors to return standardized JSON responses.
"""
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse

async def HTTP_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """
    Catches predictable HTTPExceptions and formats them uniformly.
    
    Args:
        request (Request): The incoming request.
        exc (HTTPException): The raised exception.
        
    Returns:
        JSONResponse: A standardized error payload.
    """
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "message": exc.detail,
            "path": request.url.path
        }
    )

async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Catches unpredictable 500 Internal Server Errors to prevent stack traces
    from leaking to the client.
    
    Args:
        request (Request): The incoming request.
        exc (Exception): The unhandled exception.
        
    Returns:
        JSONResponse: A generic 500 error payload.
    """
    return JSONResponse(
        status_code=500,
        content={
            "error": True,
            "message": "An unexpected server error occurred. Please try again later.",
            "path": request.url.path
        }
    )