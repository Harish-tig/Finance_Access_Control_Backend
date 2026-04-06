import functools
import asyncio
from fastapi import HTTPException, status
from app.models.user import UserRole

# Role hierarchy: Admin > Analyst > Viewer
ROLE_HIERARCHY: dict[str, set[str]] = {
    UserRole.VIEWER: {UserRole.VIEWER, UserRole.ANALYST, UserRole.ADMIN},
    UserRole.ANALYST: {UserRole.ANALYST, UserRole.ADMIN},
    UserRole.ADMIN: {UserRole.ADMIN},
}


def require_roles(*allowed_roles: str):
    """Restrict a route to users with one of the allowed roles."""
    allowed_set = set(allowed_roles)

    def decorator(func):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            user = kwargs.get("current_user")
            if user is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required.",
                )
            if user.role not in allowed_set:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Access denied. Required roles: {', '.join(allowed_set)}.",
                )
            return await func(*args, **kwargs)

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            user = kwargs.get("current_user")
            if user is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required.",
                )
            if user.role not in allowed_set:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Access denied. Required roles: {', '.join(allowed_set)}.",
                )
            return func(*args, **kwargs)

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


require_admin = require_roles(UserRole.ADMIN)
require_analyst = require_roles(UserRole.ANALYST, UserRole.ADMIN)
require_viewer = require_roles(UserRole.VIEWER, UserRole.ANALYST, UserRole.ADMIN)
