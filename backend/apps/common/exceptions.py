class ServiceNotImplementedError(NotImplementedError):
    def __init__(self, service: str) -> None:
        if not isinstance(service, str) or not service.strip():
            raise ValueError("service key is required")

        self.service = service
        super().__init__(f"{service} service is not implemented")


class ApiErrorResponseException(Exception):
    def __init__(
        self,
        code: str,
        *,
        status_code: int,
        details: dict | None = None,
    ) -> None:
        if not isinstance(code, str) or not code.strip():
            raise ValueError("error code is required")
        if not isinstance(status_code, int):
            raise ValueError("status_code must be an integer")

        self.code = code
        self.status_code = status_code
        self.details = {} if details is None else dict(details)
        super().__init__(code)
