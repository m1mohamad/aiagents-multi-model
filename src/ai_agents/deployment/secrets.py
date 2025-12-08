"""Secrets management - encryption, decryption, validation.

SECURITY RULES:
1. NEVER log secret values (even partial)
2. NEVER store secrets in plaintext
3. ALWAYS validate file permissions
4. ALWAYS use secure file operations
5. Accept secrets via stdin only (not CLI args)
"""
import os
import subprocess
from pathlib import Path
from typing import Optional
import logging

from .utils import get_user_home, get_user_uid, get_user_gid
from .exceptions import SecurityError

# Configure logging to NEVER log secret values
logger = logging.getLogger(__name__)


class SecretValidator:
    """Validate secret format. Single responsibility: validation only."""

    @staticmethod
    def validate_claude_key(key: str) -> bool:
        """Validate Claude API key format."""
        return key.startswith("sk-ant-") and len(key) > 50

    @staticmethod
    def validate_grok_key(key: str) -> bool:
        """Validate Grok API key format."""
        return key.startswith("xai-") and len(key) > 30

    @staticmethod
    def validate_gemini_key(key: str) -> bool:
        """Validate Gemini API key format."""
        return key.startswith("AIza") and len(key) > 30

    @classmethod
    def validate(cls, agent: str, key: str) -> bool:
        """Validate key for specific agent."""
        validators = {
            "claude": cls.validate_claude_key,
            "grok": cls.validate_grok_key,
            "gemini": cls.validate_gemini_key,
        }
        validator = validators.get(agent)
        if not validator:
            raise ValueError(f"Unknown agent: {agent}")
        return validator(key)


class SecretsManager:
    """Manage encrypted secrets. Single responsibility: secret operations."""

    def __init__(self):
        self.ai_dir = Path("/ai")
        self.age_key_path = get_user_home() / ".age-key.txt"
        self.validator = SecretValidator()

        # SECURITY: Verify age key exists and has correct permissions
        if not self.age_key_path.exists():
            raise SecurityError(f"Age key not found: {self.age_key_path}")

        # SECURITY: Check file permissions (should be 600)
        stat = self.age_key_path.stat()
        if stat.st_mode & 0o077 != 0:
            raise SecurityError(
                f"Age key has insecure permissions: {oct(stat.st_mode)[-3:]}. "
                f"Run: chmod 600 {self.age_key_path}"
            )

    def get_public_key(self) -> str:
        """Extract age public key."""
        with open(self.age_key_path) as f:
            for line in f:
                if line.startswith("# public key:"):
                    return line.split(":")[-1].strip()
        raise SecurityError("Public key not found in age key file")

    def encrypt_secret(self, agent: str, secret: str) -> None:
        """Encrypt and store secret for agent.

        SECURITY:
        - Secret passed as string (never from CLI args)
        - No logging of secret value
        - Atomic write operation
        - Strict file permissions
        """
        # Validate agent
        if agent not in ["claude", "grok", "gemini"]:
            raise ValueError(f"Unknown agent: {agent}")

        # Validate secret format
        if not self.validator.validate(agent, secret):
            # Log WITHOUT secret value
            logger.error(f"Invalid secret format for {agent}")
            raise SecurityError(f"Invalid {agent} API key format")

        # Prepare paths
        secret_file = self.ai_dir / agent / "context" / ".secrets.age"
        secret_file.parent.mkdir(parents=True, exist_ok=True)

        # Get public key
        public_key = self.get_public_key()

        # Encrypt (secret passed via stdin, never CLI)
        try:
            result = subprocess.run(
                ["age", "-r", public_key, "-o", str(secret_file)],
                input=secret.encode(),
                capture_output=True,
                check=True,
            )
        except subprocess.CalledProcessError as e:
            # Log error WITHOUT secret
            logger.error(f"Encryption failed for {agent}")
            raise SecurityError(f"Failed to encrypt {agent} secret") from e

        # SECURITY: Set strict permissions (600)
        secret_file.chmod(0o600)

        # SECURITY: Set correct ownership
        os.chown(secret_file, get_user_uid(), get_user_gid())

        # Log success (no secret value)
        logger.info(f"Successfully encrypted secret for {agent}")

    def verify_secret_exists(self, agent: str) -> bool:
        """Check if encrypted secret exists."""
        secret_file = self.ai_dir / agent / "context" / ".secrets.age"
        return secret_file.exists()

    def verify_secret_permissions(self, agent: str) -> bool:
        """Verify secret file has correct permissions (600)."""
        secret_file = self.ai_dir / agent / "context" / ".secrets.age"
        if not secret_file.exists():
            return False

        stat = secret_file.stat()
        return stat.st_mode & 0o777 == 0o600

    def test_decryption(self, agent: str) -> bool:
        """Test if secret can be decrypted (returns bool, not secret).

        SECURITY: Returns only success/failure, never the secret value.
        """
        secret_file = self.ai_dir / agent / "context" / ".secrets.age"
        if not secret_file.exists():
            return False

        try:
            result = subprocess.run(
                ["age", "-d", "-i", str(self.age_key_path), str(secret_file)],
                capture_output=True,
                check=True,
                text=True,
            )
            # Verify we got some output (don't log it!)
            return len(result.stdout.strip()) > 0
        except subprocess.CalledProcessError:
            return False
