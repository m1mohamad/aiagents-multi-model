"""Backup and restore operations. Single responsibility: data preservation."""
import shutil
import json
from pathlib import Path
from datetime import datetime
from typing import Optional
import logging

from .exceptions import BackupError

logger = logging.getLogger(__name__)


class BackupManager:
    """Manage backups and restores. Single responsibility: backup operations."""

    def __init__(self, backup_dir: Optional[Path] = None):
        self.backup_dir = backup_dir or Path("/tmp/ai-backups")
        self.ai_dir = Path("/ai")
        self.agents = ["claude", "grok", "gemini"]

    def create_backup(self, include_secrets: bool = True) -> Path:
        """Create timestamped backup of /ai directory.

        Returns: Path to backup directory
        Raises: BackupError on failure
        """
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        backup_path = self.backup_dir / f"ai-backup-{timestamp}"

        try:
            # Create backup directory
            backup_path.mkdir(parents=True, exist_ok=True)

            # Backup structure and history
            for agent in self.agents:
                agent_src = self.ai_dir / agent
                if not agent_src.exists():
                    logger.debug(f"Skipping {agent} - directory does not exist")
                    continue

                agent_dst = backup_path / agent

                # Always backup history
                history_src = agent_src / "history"
                if history_src.exists():
                    shutil.copytree(history_src, agent_dst / "history", dirs_exist_ok=True)
                    logger.debug(f"Backed up {agent} history")

                # Optionally backup secrets
                if include_secrets:
                    secrets_src = agent_src / "context" / ".secrets.age"
                    if secrets_src.exists():
                        secrets_dst = agent_dst / "context"
                        secrets_dst.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(secrets_src, secrets_dst / ".secrets.age")
                        logger.debug(f"Backed up {agent} secrets")

            # Create backup metadata
            metadata = backup_path / "backup.json"
            metadata.write_text(
                json.dumps(
                    {
                        "timestamp": timestamp,
                        "include_secrets": include_secrets,
                        "agents": self.agents,
                        "backup_format": "v1",
                    },
                    indent=2,
                )
            )

            logger.info(f"Backup created: {backup_path}")
            return backup_path

        except Exception as e:
            logger.error(f"Backup failed: {e}")
            # Cleanup partial backup
            if backup_path.exists():
                try:
                    shutil.rmtree(backup_path)
                except Exception as cleanup_error:
                    logger.warning(f"Failed to cleanup partial backup: {cleanup_error}")
            raise BackupError(f"Backup failed: {e}") from e

    def restore_backup(self, backup_path: Path, create_safety_backup: bool = True) -> None:
        """Restore from backup.

        SAFETY: Creates backup of current state before restoring (if enabled).
        """
        if not backup_path.exists():
            raise BackupError(f"Backup not found: {backup_path}")

        # Verify backup metadata
        metadata_file = backup_path / "backup.json"
        if not metadata_file.exists():
            raise BackupError(f"Invalid backup: missing metadata file")

        try:
            metadata = json.loads(metadata_file.read_text())
            logger.info(f"Restoring backup from {metadata.get('timestamp', 'unknown')}")
        except json.JSONDecodeError as e:
            raise BackupError(f"Invalid backup metadata: {e}") from e

        # Safety: Backup current state before restoring
        safety_backup_path = None
        if create_safety_backup and self.ai_dir.exists():
            logger.info("Creating safety backup before restore...")
            try:
                safety_backup_path = self.create_backup(include_secrets=True)
            except BackupError as e:
                logger.warning(f"Failed to create safety backup: {e}")
                # Continue anyway - user may want to restore even without safety backup

        try:
            # Restore each agent
            for agent in self.agents:
                agent_backup = backup_path / agent
                if not agent_backup.exists():
                    logger.debug(f"No backup data for {agent}")
                    continue

                agent_dst = self.ai_dir / agent

                # Restore history
                history_backup = agent_backup / "history"
                if history_backup.exists():
                    history_dst = agent_dst / "history"
                    if history_dst.exists():
                        shutil.rmtree(history_dst)
                    shutil.copytree(history_backup, history_dst)
                    logger.info(f"Restored {agent} history")

                # Restore secrets
                secrets_backup = agent_backup / "context" / ".secrets.age"
                if secrets_backup.exists():
                    secrets_dst = agent_dst / "context"
                    secrets_dst.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(secrets_backup, secrets_dst / ".secrets.age")
                    logger.info(f"Restored {agent} secrets")

            logger.info(f"Restored from: {backup_path}")
            if safety_backup_path:
                logger.info(f"Safety backup at: {safety_backup_path}")

        except Exception as e:
            logger.error(f"Restore failed: {e}")
            if safety_backup_path:
                logger.info(f"Safety backup preserved at: {safety_backup_path}")
            raise BackupError(f"Restore failed: {e}") from e

    def list_backups(self) -> list[Path]:
        """List available backups, newest first."""
        if not self.backup_dir.exists():
            return []

        backups = sorted(
            self.backup_dir.glob("ai-backup-*"), key=lambda p: p.stat().st_mtime, reverse=True
        )
        return backups

    def get_backup_info(self, backup_path: Path) -> dict:
        """Get backup metadata information."""
        if not backup_path.exists():
            raise BackupError(f"Backup not found: {backup_path}")

        metadata_file = backup_path / "backup.json"
        if not metadata_file.exists():
            return {
                "path": str(backup_path),
                "exists": True,
                "has_metadata": False,
                "error": "Missing metadata file",
            }

        try:
            metadata = json.loads(metadata_file.read_text())
            return {
                "path": str(backup_path),
                "exists": True,
                "has_metadata": True,
                "timestamp": metadata.get("timestamp"),
                "include_secrets": metadata.get("include_secrets"),
                "agents": metadata.get("agents"),
                "backup_format": metadata.get("backup_format"),
            }
        except Exception as e:
            return {
                "path": str(backup_path),
                "exists": True,
                "has_metadata": False,
                "error": str(e),
            }

    def delete_backup(self, backup_path: Path) -> None:
        """Delete a backup directory."""
        if not backup_path.exists():
            raise BackupError(f"Backup not found: {backup_path}")

        try:
            shutil.rmtree(backup_path)
            logger.info(f"Deleted backup: {backup_path}")
        except Exception as e:
            raise BackupError(f"Failed to delete backup: {e}") from e
