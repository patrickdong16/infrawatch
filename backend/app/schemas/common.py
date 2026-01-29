"""Common Pydantic schemas."""

from typing import Any, Generic, Optional, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class APIResponse(BaseModel, Generic[T]):
    """Standard API response wrapper."""
    success: bool = True
    data: Optional[T] = None
    meta: Optional[dict[str, Any]] = None


class ErrorDetail(BaseModel):
    """Error detail schema."""
    code: str
    message: str
    details: Optional[dict[str, Any]] = None


class ErrorResponse(BaseModel):
    """Error response schema."""
    success: bool = False
    error: ErrorDetail
    request_id: Optional[str] = None


class PaginationParams(BaseModel):
    """Pagination parameters."""
    limit: int = 20
    offset: int = 0


class PaginationMeta(BaseModel):
    """Pagination metadata."""
    total: int
    limit: int
    offset: int
    has_more: bool
