class AppError(Exception):
    status_code = 500
    code = "internal_error"

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class UpstreamTimeoutError(AppError):
    status_code = 504
    code = "upstream_timeout"


class UpstreamError(AppError):
    status_code = 502
    code = "upstream_unavailable"


class RateLimitError(AppError):
    status_code = 429
    code = "rate_limited"
