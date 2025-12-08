"""Deployment state detection - READ ONLY, no modifications."""
import subprocess
from pathlib import Path
from dataclasses import dataclass
from typing import Optional
import logging

from .utils import get_user_home

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class DeploymentState:
    """Immutable state representation."""

    containers_running: bool
    age_key_exists: bool
    secrets_configured: dict[str, bool]  # {agent: has_secret}
    history_dirs_exist: bool
    python_package_installed: bool

    @property
    def is_fresh_install(self) -> bool:
        """No containers or structure exists."""
        return not self.containers_running and not self.history_dirs_exist

    @property
    def needs_secrets(self) -> bool:
        """Some agents missing secrets."""
        return not all(self.secrets_configured.values())

    @property
    def is_fully_deployed(self) -> bool:
        """Everything installed and configured."""
        return (
            self.containers_running
            and self.age_key_exists
            and all(self.secrets_configured.values())
            and self.python_package_installed
        )


class StateDetector:
    """Detect current deployment state. READ ONLY."""

    def __init__(self):
        self.ai_dir = Path("/ai")
        self.agents = ["claude", "grok", "gemini"]

    def detect(self) -> DeploymentState:
        """Detect current state. No side effects."""
        return DeploymentState(
            containers_running=self._check_containers(),
            age_key_exists=self._check_age_key(),
            secrets_configured=self._check_secrets(),
            history_dirs_exist=self._check_history_dirs(),
            python_package_installed=self._check_python_package(),
        )

    def _check_containers(self) -> bool:
        """Check if ai-agents pod is running."""
        try:
            result = subprocess.run(
                ["podman", "pod", "exists", "ai-agents"],
                capture_output=True,
                timeout=5,
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False

    def _check_age_key(self) -> bool:
        """Check if age key exists for current user."""
        user_home = get_user_home()
        age_key_path = user_home / ".age-key.txt"
        return age_key_path.exists()

    def _check_secrets(self) -> dict[str, bool]:
        """Check which agents have encrypted secrets."""
        secrets = {}
        for agent in self.agents:
            secret_file = self.ai_dir / agent / "context" / ".secrets.age"
            secrets[agent] = secret_file.exists()
        return secrets

    def _check_history_dirs(self) -> bool:
        """Check if history directories exist."""
        if not self.ai_dir.exists():
            return False
        for agent in self.agents:
            if not (self.ai_dir / agent / "history").exists():
                return False
        return True

    def _check_python_package(self) -> bool:
        """Check if Python package installed in containers."""
        try:
            result = subprocess.run(
                [
                    "podman",
                    "exec",
                    "claude-agent",
                    "python3",
                    "-c",
                    "import ai_agents; print(ai_agents.__version__)",
                ],
                capture_output=True,
                text=True,
                timeout=5,
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
