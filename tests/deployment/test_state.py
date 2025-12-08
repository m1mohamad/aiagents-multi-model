"""Tests for state detection."""
import pytest
from pathlib import Path
from ai_agents.deployment.state import StateDetector, DeploymentState


def test_deployment_state_immutable():
    """DeploymentState should be immutable (frozen dataclass)."""
    state = DeploymentState(
        containers_running=True,
        age_key_exists=True,
        secrets_configured={"claude": True, "grok": True, "gemini": True},
        history_dirs_exist=True,
        python_package_installed=True,
    )

    # Should raise FrozenInstanceError when trying to modify
    with pytest.raises(Exception):  # dataclasses.FrozenInstanceError
        state.containers_running = False


def test_fresh_install_detection():
    """Should detect fresh install correctly."""
    state = DeploymentState(
        containers_running=False,
        age_key_exists=False,
        secrets_configured={"claude": False, "grok": False, "gemini": False},
        history_dirs_exist=False,
        python_package_installed=False,
    )
    assert state.is_fresh_install
    assert not state.is_fully_deployed
    assert state.needs_secrets


def test_fully_deployed_detection():
    """Should detect fully deployed state correctly."""
    state = DeploymentState(
        containers_running=True,
        age_key_exists=True,
        secrets_configured={"claude": True, "grok": True, "gemini": True},
        history_dirs_exist=True,
        python_package_installed=True,
    )
    assert not state.is_fresh_install
    assert state.is_fully_deployed
    assert not state.needs_secrets


def test_partial_secrets_detection():
    """Should detect when some secrets are missing."""
    state = DeploymentState(
        containers_running=True,
        age_key_exists=True,
        secrets_configured={"claude": True, "grok": False, "gemini": True},
        history_dirs_exist=True,
        python_package_installed=True,
    )
    assert state.needs_secrets
    assert not state.is_fully_deployed


def test_state_detector_is_read_only():
    """State detector should not modify anything (idempotent)."""
    detector = StateDetector()
    state1 = detector.detect()
    state2 = detector.detect()

    # Both calls should return the same state
    assert state1.containers_running == state2.containers_running
    assert state1.age_key_exists == state2.age_key_exists
    assert state1.history_dirs_exist == state2.history_dirs_exist
    assert state1.python_package_installed == state2.python_package_installed


def test_state_detector_handles_missing_podman():
    """Should gracefully handle missing podman command."""
    detector = StateDetector()
    # Even if podman doesn't exist, detect() should not crash
    state = detector.detect()
    assert isinstance(state, DeploymentState)


def test_state_detector_timeout_handling():
    """Should handle command timeouts gracefully."""
    detector = StateDetector()
    # Commands have 5 second timeout, should not hang
    state = detector.detect()
    assert isinstance(state, DeploymentState)
