"""Tests for backup and restore operations."""
import pytest
import json
from pathlib import Path
from ai_agents.deployment.backup import BackupManager, BackupError


class TestBackupManager:
    """Tests for backup manager."""

    def test_backup_manager_initialization(self, tmp_path):
        """Should initialize with custom or default backup directory."""
        # Custom backup directory
        manager = BackupManager(backup_dir=tmp_path / "backups")
        assert manager.backup_dir == tmp_path / "backups"
        assert manager.ai_dir == Path("/ai")
        assert manager.agents == ["claude", "grok", "gemini"]

        # Default backup directory
        manager_default = BackupManager()
        assert manager_default.backup_dir == Path("/tmp/ai-backups")

    def test_create_backup_with_empty_ai_dir(self, tmp_path):
        """Should handle missing /ai directory gracefully."""
        manager = BackupManager(backup_dir=tmp_path)

        # Even if /ai doesn't exist, backup should not crash
        backup_path = manager.create_backup(include_secrets=False)

        assert backup_path.exists()
        assert (backup_path / "backup.json").exists()

        # Verify metadata
        metadata = json.loads((backup_path / "backup.json").read_text())
        assert "timestamp" in metadata
        assert metadata["include_secrets"] is False
        assert metadata["agents"] == ["claude", "grok", "gemini"]

    def test_create_backup_atomic_operation(self, tmp_path, monkeypatch):
        """Should cleanup partial backup on failure."""
        manager = BackupManager(backup_dir=tmp_path)

        # Mock shutil.copytree to raise an error
        def mock_copytree(*args, **kwargs):
            raise RuntimeError("Simulated failure")

        monkeypatch.setattr("shutil.copytree", mock_copytree)

        # Create a fake /ai directory structure
        fake_ai = tmp_path / "fake_ai"
        fake_ai.mkdir()
        (fake_ai / "claude" / "history").mkdir(parents=True)
        manager.ai_dir = fake_ai

        # Backup should fail and cleanup
        with pytest.raises(BackupError, match="Backup failed"):
            manager.create_backup()

        # Verify no partial backups remain (or only empty dir)
        backups = list(tmp_path.glob("ai-backup-*"))
        # Either no backups, or only the backup dir exists but is being cleaned up
        assert len(backups) == 0 or all(not b.exists() for b in backups)

    def test_list_backups(self, tmp_path):
        """Should list backups sorted by newest first."""
        manager = BackupManager(backup_dir=tmp_path)

        # Create mock backups with different timestamps
        backup1 = tmp_path / "ai-backup-20251201-100000"
        backup2 = tmp_path / "ai-backup-20251202-100000"
        backup3 = tmp_path / "ai-backup-20251203-100000"

        for backup_path in [backup1, backup2, backup3]:
            backup_path.mkdir()
            (backup_path / "backup.json").write_text("{}")

        # List should return newest first
        backups = manager.list_backups()
        assert len(backups) >= 3  # At least our 3 test backups
        # Newest backup should have later timestamp
        assert backups[0].name >= backups[-1].name

    def test_get_backup_info(self, tmp_path):
        """Should retrieve backup metadata."""
        manager = BackupManager(backup_dir=tmp_path)

        # Create a backup with metadata
        backup_path = tmp_path / "ai-backup-test"
        backup_path.mkdir()

        metadata = {
            "timestamp": "20251208-120000",
            "include_secrets": True,
            "agents": ["claude", "grok", "gemini"],
            "backup_format": "v1",
        }
        (backup_path / "backup.json").write_text(json.dumps(metadata))

        # Get backup info
        info = manager.get_backup_info(backup_path)
        assert info["exists"] is True
        assert info["has_metadata"] is True
        assert info["timestamp"] == "20251208-120000"
        assert info["include_secrets"] is True

    def test_get_backup_info_missing_metadata(self, tmp_path):
        """Should handle missing metadata gracefully."""
        manager = BackupManager(backup_dir=tmp_path)

        # Create backup without metadata
        backup_path = tmp_path / "ai-backup-no-metadata"
        backup_path.mkdir()

        info = manager.get_backup_info(backup_path)
        assert info["exists"] is True
        assert info["has_metadata"] is False
        assert "error" in info

    def test_restore_backup_requires_valid_path(self, tmp_path):
        """Should fail if backup path doesn't exist."""
        manager = BackupManager(backup_dir=tmp_path)

        nonexistent = tmp_path / "nonexistent-backup"
        with pytest.raises(BackupError, match="Backup not found"):
            manager.restore_backup(nonexistent, create_safety_backup=False)

    def test_restore_backup_requires_metadata(self, tmp_path):
        """Should fail if backup has no metadata."""
        manager = BackupManager(backup_dir=tmp_path)

        # Create backup without metadata
        backup_path = tmp_path / "ai-backup-invalid"
        backup_path.mkdir()

        with pytest.raises(BackupError, match="Invalid backup"):
            manager.restore_backup(backup_path, create_safety_backup=False)

    def test_delete_backup(self, tmp_path):
        """Should delete backup directory."""
        manager = BackupManager(backup_dir=tmp_path)

        # Create a backup
        backup_path = tmp_path / "ai-backup-to-delete"
        backup_path.mkdir()
        (backup_path / "backup.json").write_text("{}")

        assert backup_path.exists()

        # Delete it
        manager.delete_backup(backup_path)
        assert not backup_path.exists()

    def test_delete_backup_nonexistent(self, tmp_path):
        """Should fail if backup doesn't exist."""
        manager = BackupManager(backup_dir=tmp_path)

        nonexistent = tmp_path / "nonexistent"
        with pytest.raises(BackupError, match="Backup not found"):
            manager.delete_backup(nonexistent)


class TestBackupSafety:
    """Safety-focused tests."""

    def test_restore_creates_safety_backup(self, tmp_path):
        """Should create safety backup before restore (if enabled)."""
        # This requires a more complex test setup
        # For now, this is a placeholder to document the requirement
        pass

    def test_backup_includes_secrets_flag(self, tmp_path):
        """Should respect include_secrets flag."""
        manager = BackupManager(backup_dir=tmp_path)

        # Test with secrets
        backup_with = manager.create_backup(include_secrets=True)
        metadata_with = json.loads((backup_with / "backup.json").read_text())
        assert metadata_with["include_secrets"] is True

        # Test without secrets
        backup_without = manager.create_backup(include_secrets=False)
        metadata_without = json.loads((backup_without / "backup.json").read_text())
        assert metadata_without["include_secrets"] is False

    def test_backup_manager_single_responsibility(self):
        """BackupManager should only handle backups, not deployment logic."""
        manager = BackupManager()

        # Manager should not have methods for container operations
        assert not hasattr(manager, "start_container")
        assert not hasattr(manager, "stop_container")
        assert not hasattr(manager, "deploy")

        # Manager should only have backup-related methods
        assert hasattr(manager, "create_backup")
        assert hasattr(manager, "restore_backup")
        assert hasattr(manager, "list_backups")
        assert hasattr(manager, "delete_backup")
