from fastapi import HTTPException


def bad_request(message: str, details: dict | None = None) -> HTTPException:
    return HTTPException(status_code=400, detail={"error": {"code": "bad_request", "message": message, "details": details or {}}})


def not_found(message: str = "Not found") -> HTTPException:
    return HTTPException(status_code=404, detail={"error": {"code": "not_found", "message": message, "details": {}}})
