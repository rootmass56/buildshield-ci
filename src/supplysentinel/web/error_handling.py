from __future__ import annotations

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse, PlainTextResponse
from starlette.responses import Response

from supplysentinel.web.logging_utils import (
    REQUEST_ID_HEADER,
    log_internal_failure,
    log_unhandled_exception,
)


GENERIC_INTERNAL_ERROR_DETAIL = "Internal server error."

_SAFE_OPERATION_DETAILS = {
    "scan": "Repository scan failed.",
    "inventory": "Dependency inventory failed.",
    "vulnerability_intelligence": "Vulnerability intelligence failed.",
    "compare": "Repository comparison failed.",
}


def safe_internal_error(
    operation: str,
    error: Exception | None = None,
) -> HTTPException:
    if error is not None:
        log_internal_failure(
            operation=operation,
            error=error,
        )

    detail = _SAFE_OPERATION_DETAILS.get(
        operation,
        GENERIC_INTERNAL_ERROR_DETAIL,
    )

    return HTTPException(
        status_code=500,
        detail=detail,
    )


async def safe_unhandled_exception_handler(
    request: Request,
    error: Exception,
) -> Response:
    request_id = log_unhandled_exception(
        request=request,
        error=error,
    )

    headers = {
        REQUEST_ID_HEADER: request_id,
        "Cache-Control": "no-store",
    }

    if request.url.path.startswith("/api/"):
        return JSONResponse(
            status_code=500,
            content={"detail": GENERIC_INTERNAL_ERROR_DETAIL},
            headers=headers,
        )

    return PlainTextResponse(
        status_code=500,
        content=GENERIC_INTERNAL_ERROR_DETAIL,
        headers=headers,
    )
