class ServiceNotImplementedError(NotImplementedError):
    def __init__(self, service: str) -> None:
        if not isinstance(service, str) or not service.strip():
            raise ValueError("service key is required")

        self.service = service
        super().__init__(f"{service} service is not implemented")
