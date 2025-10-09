"""Common provider exceptions."""


class ProviderServiceError(RuntimeError):
    """Raised when an upstream provider cannot fulfil a request."""


class ProviderDataError(ProviderServiceError):
    """Raised when data returned by an upstream provider is invalid."""
