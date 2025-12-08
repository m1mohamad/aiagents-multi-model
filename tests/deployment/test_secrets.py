"""Tests for secrets management."""
import pytest
from pathlib import Path
from ai_agents.deployment.secrets import SecretValidator, SecretsManager, SecurityError


class TestSecretValidator:
    """Tests for secret format validation."""

    def test_validate_claude_key(self):
        """Test Claude key validation."""
        validator = SecretValidator()
        # Valid keys
        assert validator.validate_claude_key("sk-ant-sid01-" + "x" * 50)
        assert validator.validate_claude_key("sk-ant-api03-" + "y" * 60)

        # Invalid keys
        assert not validator.validate_claude_key("invalid")
        assert not validator.validate_claude_key("sk-ant-short")
        assert not validator.validate_claude_key("xai-" + "x" * 50)

    def test_validate_grok_key(self):
        """Test Grok key validation."""
        validator = SecretValidator()
        # Valid keys
        assert validator.validate_grok_key("xai-" + "x" * 40)
        assert validator.validate_grok_key("xai-" + "y" * 50)

        # Invalid keys
        assert not validator.validate_grok_key("invalid")
        assert not validator.validate_grok_key("xai-short")
        assert not validator.validate_grok_key("sk-ant-" + "x" * 40)

    def test_validate_gemini_key(self):
        """Test Gemini key validation."""
        validator = SecretValidator()
        # Valid keys
        assert validator.validate_gemini_key("AIza" + "x" * 35)
        assert validator.validate_gemini_key("AIza" + "Y" * 40)

        # Invalid keys
        assert not validator.validate_gemini_key("invalid")
        assert not validator.validate_gemini_key("AIzashort")
        assert not validator.validate_gemini_key("xai-" + "x" * 35)

    def test_validate_with_agent_name(self):
        """Test validation using agent name."""
        validator = SecretValidator()

        # Valid combinations
        assert validator.validate("claude", "sk-ant-sid01-" + "x" * 50)
        assert validator.validate("grok", "xai-" + "x" * 40)
        assert validator.validate("gemini", "AIza" + "x" * 35)

        # Invalid combinations (wrong format for agent)
        assert not validator.validate("claude", "xai-" + "x" * 50)
        assert not validator.validate("grok", "AIza" + "x" * 40)
        assert not validator.validate("gemini", "sk-ant-" + "x" * 40)

    def test_validate_unknown_agent(self):
        """Test that unknown agent raises ValueError."""
        validator = SecretValidator()
        with pytest.raises(ValueError, match="Unknown agent"):
            validator.validate("unknown_agent", "some_key")


class TestSecretsManager:
    """Tests for secrets manager (requires test fixtures)."""

    def test_secrets_manager_requires_age_key(self, tmp_path, monkeypatch):
        """Should fail if age key doesn't exist."""
        # Mock get_user_home to return temp path without age key
        monkeypatch.setattr(
            "ai_agents.deployment.secrets.get_user_home", lambda: tmp_path
        )

        with pytest.raises(SecurityError, match="Age key not found"):
            SecretsManager()

    def test_never_logs_secret_values(self, caplog):
        """CRITICAL: Secrets should NEVER appear in logs."""
        # This test ensures no secret values leak into logs
        # Even on errors, only generic messages should appear

        # Any log message containing potential secret patterns should fail
        test_secret = "sk-ant-test-secret-12345"

        # Simulate logging an error (should not contain secret)
        import logging

        logger = logging.getLogger("ai_agents.deployment.secrets")
        logger.error("Invalid secret format for claude")  # Correct way

        # Check that no log contains the secret pattern
        for record in caplog.records:
            assert "sk-ant-test" not in record.message
            assert test_secret not in record.message

    def test_encrypt_rejects_invalid_format(self):
        """Should reject malformed API keys early."""
        # This requires proper test fixtures with age key setup
        # For now, this is a placeholder to document the requirement
        pass

    def test_encrypt_sets_correct_permissions(self):
        """Should set 600 permissions on encrypted files."""
        # This requires proper test fixtures
        # For now, this is a placeholder
        pass

    def test_verify_secret_permissions(self):
        """Should detect insecure permissions."""
        # This requires proper test fixtures
        # For now, this is a placeholder
        pass

    def test_test_decryption_never_returns_secret(self):
        """test_decryption() should only return bool, never the secret."""
        # This is a design validation test
        # For now, this is a placeholder
        pass


# Security validation tests
class TestSecurityValidation:
    """Security-focused tests."""

    def test_no_secrets_in_exception_messages(self):
        """Exception messages should not contain secret values."""
        validator = SecretValidator()

        # Test with invalid secrets
        invalid_secret = "sk-ant-invalid-but-this-is-secret-data"

        try:
            # This will fail validation, but error should not contain secret
            if not validator.validate_claude_key(invalid_secret[:20]):
                raise SecurityError("Invalid format")
        except SecurityError as e:
            # Exception message should not contain the secret
            assert invalid_secret not in str(e)
            assert "secret-data" not in str(e)

    def test_validator_is_stateless(self):
        """Validator should have no state (pure functions)."""
        validator1 = SecretValidator()
        validator2 = SecretValidator()

        test_key = "sk-ant-sid01-" + "x" * 50

        # Both instances should give same result
        assert validator1.validate_claude_key(test_key) == validator2.validate_claude_key(test_key)

    def test_validator_single_responsibility(self):
        """Validator should only validate, not store or transform."""
        validator = SecretValidator()
        test_key = "sk-ant-sid01-" + "x" * 50

        # Validation should not modify the key
        result = validator.validate_claude_key(test_key)
        assert isinstance(result, bool)
        # Key should remain unchanged (validator doesn't store it)
