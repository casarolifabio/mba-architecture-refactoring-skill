from middlewares.error_handler import (
    register_error_handlers,
    NotFoundError,
    UnauthorizedError,
    ForbiddenError,
)

__all__ = [
    "register_error_handlers",
    "NotFoundError",
    "UnauthorizedError",
    "ForbiddenError",
]
