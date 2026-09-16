from typing import Any


class ApplicationError(Exception):
    status_code = 500
    code = "internal_error"
    message = "An unexpected error occurred."

    def __init__(
        self,
        *,
        code: str | None = None,
        message: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        self.code = code or self.code
        self.message = message or self.message
        self.details = details
        super().__init__(self.message)


class NotFoundError(ApplicationError):
    status_code = 404
    code = "resource_not_found"
    message = "The requested resource was not found."


class ConflictError(ApplicationError):
    status_code = 409
    code = "resource_conflict"
    message = "The request conflicts with the current resource state."


class BusinessRuleError(ApplicationError):
    status_code = 422
    code = "business_rule_violation"
    message = "The request violates a business rule."
