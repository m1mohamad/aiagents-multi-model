"""
AI Agents Deployment Package

Python-based deployment tools for secure, stable container management.
Follows Single Responsibility Principle and security-first approach.

SECURITY UPDATE: BackupManager has been replaced with SecureBackupManager
- Old: Unencrypted backups in /tmp (backup_legacy.py)
- New: Encrypted backups in ~/ai-backups (backup.py)
"""

from .state import DeploymentState, StateDetector
from .secrets import SecretValidator, SecretsManager
from .backup import SecureBackupManager
from .backup_legacy import BackupManager  # Deprecated: Use SecureBackupManager
from .containers import ContainerManager, ContainerInfo
from .exceptions import (
    DeploymentError,
    StateError,
    SecurityError,
    BackupError,
    ContainerError,
)

__all__ = [
    "DeploymentState",
    "StateDetector",
    "SecretValidator",
    "SecretsManager",
    "SecureBackupManager",  # Primary backup manager
    "BackupManager",  # Deprecated: Legacy unencrypted backups
    "ContainerManager",
    "ContainerInfo",
    "DeploymentError",
    "StateError",
    "SecurityError",
    "BackupError",
    "ContainerError",
]
