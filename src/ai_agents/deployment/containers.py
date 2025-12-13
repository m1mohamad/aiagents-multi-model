"""Container operations module. Single responsibility: container lifecycle management.

SECURITY:
- Validates container names
- Timeout protection for all operations
- Graceful error handling
- No secret exposure in logs

OPERATIONS:
- Start/stop/restart containers
- Check container status
- Execute commands in containers
- List containers and pods
"""
import subprocess
import logging
from pathlib import Path
from typing import Optional, List
from dataclasses import dataclass

from .exceptions import ContainerError
from .utils import get_user_uid, get_user_gid

logger = logging.getLogger(__name__)


@dataclass
class ContainerInfo:
    """Container information."""

    name: str
    status: str  # running, stopped, created, etc.
    pod: Optional[str]
    image: str


class ContainerManager:
    """Manage container operations. Single responsibility: container lifecycle."""

    def __init__(self):
        self.agents = ["claude", "grok", "gemini"]
        self.pod_name = "ai-agents"
        self.timeout = 30  # seconds

    def _validate_agent(self, agent: str) -> None:
        """Validate agent name to prevent command injection."""
        if agent not in self.agents:
            raise ValueError(f"Invalid agent name: {agent}. Must be one of {self.agents}")

    def _run_podman(self, args: List[str], timeout: Optional[int] = None) -> subprocess.CompletedProcess:
        """Run podman command with timeout and error handling.

        Args:
            args: Command arguments (e.g., ["pod", "exists", "ai-agents"])
            timeout: Optional timeout in seconds (default: self.timeout)

        Returns:
            CompletedProcess with stdout/stderr

        Raises:
            ContainerError: On command failure or timeout
        """
        timeout = timeout or self.timeout
        cmd = ["podman"] + args

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False,  # We handle errors manually
            )
            return result
        except subprocess.TimeoutExpired as e:
            logger.error(f"Podman command timed out after {timeout}s: {' '.join(args)}")
            raise ContainerError(f"Container operation timed out: {' '.join(args)}") from e
        except FileNotFoundError as e:
            logger.error("Podman command not found. Is podman installed?")
            raise ContainerError("Podman not found. Install with: apt install podman") from e

    def pod_exists(self) -> bool:
        """Check if ai-agents pod exists."""
        result = self._run_podman(["pod", "exists", self.pod_name])
        return result.returncode == 0

    def is_pod_running(self) -> bool:
        """Check if pod is running (not just exists)."""
        if not self.pod_exists():
            return False

        result = self._run_podman(["pod", "ps", "--filter", f"name={self.pod_name}", "--format", "{{.Status}}"])
        if result.returncode != 0:
            return False

        return "Running" in result.stdout

    def container_exists(self, agent: str) -> bool:
        """Check if agent container exists."""
        self._validate_agent(agent)
        container_name = f"{agent}-agent"
        result = self._run_podman(["container", "exists", container_name])
        return result.returncode == 0

    def is_container_running(self, agent: str) -> bool:
        """Check if agent container is running."""
        self._validate_agent(agent)
        if not self.container_exists(agent):
            return False

        container_name = f"{agent}-agent"
        result = self._run_podman(["ps", "--filter", f"name={container_name}", "--format", "{{.Names}}"])

        if result.returncode != 0:
            return False

        return container_name in result.stdout

    def start_container(self, agent: str) -> bool:
        """Start agent container."""
        self._validate_agent(agent)
        container_name = f"{agent}-agent"

        if self.is_container_running(agent):
            logger.info(f"{container_name} already running")
            return True

        if not self.container_exists(agent):
            logger.error(f"{container_name} does not exist")
            return False

        logger.info(f"Starting {container_name}...")
        result = self._run_podman(["start", container_name])

        if result.returncode == 0:
            logger.info(f"✓ {container_name} started")
            return True
        else:
            logger.error(f"Failed to start {container_name}: {result.stderr}")
            return False

    def stop_container(self, agent: str, timeout: int = 10) -> bool:
        """Stop agent container gracefully."""
        self._validate_agent(agent)
        container_name = f"{agent}-agent"

        if not self.is_container_running(agent):
            logger.info(f"{container_name} already stopped")
            return True

        logger.info(f"Stopping {container_name}...")
        result = self._run_podman(["stop", "-t", str(timeout), container_name])

        if result.returncode == 0:
            logger.info(f"✓ {container_name} stopped")
            return True
        else:
            logger.error(f"Failed to stop {container_name}: {result.stderr}")
            return False

    def restart_container(self, agent: str) -> bool:
        """Restart agent container."""
        self._validate_agent(agent)
        container_name = f"{agent}-agent"

        if not self.container_exists(agent):
            logger.error(f"{container_name} does not exist")
            return False

        logger.info(f"Restarting {container_name}...")
        result = self._run_podman(["restart", container_name])

        if result.returncode == 0:
            logger.info(f"✓ {container_name} restarted")
            return True
        else:
            logger.error(f"Failed to restart {container_name}: {result.stderr}")
            return False
    def exec_in_container(
        self,
        agent: str,
        command: List[str],
        timeout: Optional[int] = None,
        check: bool = False,
    ) -> subprocess.CompletedProcess:
        """Execute command in agent container."""
        self._validate_agent(agent)
        container_name = f"{agent}-agent"

        if not self.is_container_running(agent):
            raise ContainerError(f"{container_name} is not running")

        podman_args = ["exec", container_name] + command
        result = self._run_podman(podman_args, timeout=timeout)

        if check and result.returncode != 0:
            raise ContainerError(
                f"Command failed in {container_name}: {' '.join(command)}\n" f"stderr: {result.stderr}"
            )

        return result

    def start_pod(self) -> bool:
        """Start the ai-agents pod."""
        if not self.pod_exists():
            logger.error(f"Pod {self.pod_name} does not exist")
            return False

        if self.is_pod_running():
            logger.info(f"Pod {self.pod_name} already running")
            return True

        logger.info(f"Starting pod {self.pod_name}...")
        result = self._run_podman(["pod", "start", self.pod_name])

        if result.returncode == 0:
            logger.info(f"✓ Pod {self.pod_name} started")
            return True
        else:
            logger.error(f"Failed to start pod: {result.stderr}")
            return False

    def stop_pod(self, timeout: int = 10) -> bool:
        """Stop the ai-agents pod."""
        if not self.pod_exists():
            logger.info(f"Pod {self.pod_name} does not exist")
            return True

        if not self.is_pod_running():
            logger.info(f"Pod {self.pod_name} already stopped")
            return True

        logger.info(f"Stopping pod {self.pod_name}...")
        result = self._run_podman(["pod", "stop", "-t", str(timeout), self.pod_name])

        if result.returncode == 0:
            logger.info(f"✓ Pod {self.pod_name} stopped")
            return True
        else:
            logger.error(f"Failed to stop pod: {result.stderr}")
            return False

    def restart_pod(self) -> bool:
        """Restart the ai-agents pod."""
        if not self.pod_exists():
            logger.error(f"Pod {self.pod_name} does not exist")
            return False

        logger.info(f"Restarting pod {self.pod_name}...")
        result = self._run_podman(["pod", "restart", self.pod_name])

        if result.returncode == 0:
            logger.info(f"✓ Pod {self.pod_name} restarted")
            return True
        else:
            logger.error(f"Failed to restart pod: {result.stderr}")
            return False

    def get_container_info(self, agent: str) -> Optional[ContainerInfo]:
        """Get detailed container information."""
        self._validate_agent(agent)
        if not self.container_exists(agent):
            return None

        container_name = f"{agent}-agent"
        result = self._run_podman(
            [
                "inspect",
                container_name,
                "--format",
                "{{.Name}}|{{.State.Status}}|{{.Pod}}|{{.ImageName}}",
            ]
        )

        if result.returncode != 0:
            return None

        try:
            name, status, pod, image = result.stdout.strip().split("|")
            return ContainerInfo(
                name=name.lstrip("/"),
                status=status,
                pod=pod if pod else None,
                image=image,
            )
        except ValueError:
            logger.warning(f"Failed to parse container info for {agent}")
            return None

    def list_all_containers(self) -> List[ContainerInfo]:
        """List all containers in the ai-agents pod."""
        containers = []
        for agent in self.agents:
            info = self.get_container_info(agent)
            if info:
                containers.append(info)
        return containers
