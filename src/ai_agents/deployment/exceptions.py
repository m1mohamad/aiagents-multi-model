"""Custom exceptions for deployment operations."""


class DeploymentError(Exception):
    """Base exception for deployment operations."""

    pass


class StateError(DeploymentError):
    """Invalid deployment state."""

    pass


class SecurityError(DeploymentError):
    """Security violation detected."""

    pass


class BackupError(DeploymentError):
    """Backup operation failed."""

    pass


class ContainerError(DeploymentError):
    """Container operation failed."""

    pass
