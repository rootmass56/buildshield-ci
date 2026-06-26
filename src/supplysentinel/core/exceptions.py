class SupplySentinelError(Exception):
    """Base exception for SupplySentinel."""


class InvalidTargetError(SupplySentinelError):
    """Raised when the scan target is invalid."""


class ScannerExecutionError(SupplySentinelError):
    """Raised when the scanner fails during execution."""