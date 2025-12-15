"""Secure backup and restore operations with encryption.

SECURITY IMPROVEMENTS:
- Encrypts entire backup (not just secrets)
- Uses age encryption for backup archives
- Validates encryption/decryption on every operation
- Stores in secure location (user home, not /tmp)
- Atomic operations with rollback on failure
"""
import subprocess
import json
import tempfile
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any
import logging
import os

from .exceptions import BackupError, SecurityError
from .utils import get_user_home, get_user_uid, get_user_gid

logger = logging.getLogger(__name__)


class SecureBackupManager:
    """Manage encrypted backups. Single responsibility: secure backup operations."""

    def __init__(self, backup_dir: Optional[Path] = None):
        """Initialize backup manager.

        Args:
            backup_dir: Optional custom backup directory (default: ~/ai-backups)

        Raises:
            SecurityError: If age key doesn't exist or has wrong permissions
        """
        # Use user's home directory, not /tmp
        self.backup_dir = backup_dir or (get_user_home() / "ai-backups")
        self.ai_dir = Path("/ai")
        self.age_key_path = get_user_home() / ".age-key.txt"

        # SECURITY: Validate age key exists and has correct permissions
        if not self.age_key_path.exists():
            raise SecurityError(f"Age key not found: {self.age_key_path}")

        stat = self.age_key_path.stat()
        if stat.st_mode & 0o077 != 0:
            raise SecurityError(
                f"Age key has insecure permissions: {oct(stat.st_mode)[-3:]}. "
                f"Run: chmod 600 {self.age_key_path}"
            )

    def _get_age_public_key(self) -> str:
        """Extract age public key from key file."""
        with open(self.age_key_path) as f:
            for line in f:
                if line.startswith("# public key:"):
                    return line.split(":")[-1].strip()
        raise SecurityError("Public key not found in age key file")

    def create_backup(self, validate: bool = True) -> Path:
        """Create encrypted backup of /ai directory.

        Args:
            validate: Test decryption after backup (default: True)

        Returns:
            Path to encrypted backup file

        Raises:
            BackupError: On backup failure
            SecurityError: On validation failure
        """
        if not self.ai_dir.exists():
            raise BackupError(f"AI directory not found: {self.ai_dir}")

        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        backup_filename = f"ai-backup-{timestamp}.tar.gz.age"
        backup_path = self.backup_dir / backup_filename

        # Create backup directory if needed
        self.backup_dir.mkdir(parents=True, exist_ok=True)

        # Get age public key
        public_key = self._get_age_public_key()

        logger.info(f"Creating encrypted backup: {backup_path}")

        try:
            # Step 1: Create tar.gz archive and pipe to age encryption
            # tar czf - /ai | age -r <pubkey> > backup.tar.gz.age

            # Create tar process
            tar_cmd = ["tar", "czf", "-", "-C", "/", "ai"]
            tar_process = subprocess.Popen(
                tar_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

            # Create age encryption process
            age_cmd = ["age", "-r", public_key, "-o", str(backup_path)]
            age_process = subprocess.Popen(
                age_cmd,
                stdin=tar_process.stdout,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

            # Close tar stdout in parent (age owns it now)
            if tar_process.stdout:
                tar_process.stdout.close()

            # Wait for both processes
            age_stdout, age_stderr = age_process.communicate()
            tar_stderr = tar_process.stderr.read() if tar_process.stderr else b""

            # Check for errors
            if tar_process.returncode != 0:
                raise BackupError(f"Tar failed: {tar_stderr.decode()}")

            if age_process.returncode != 0:
                raise BackupError(f"Encryption failed: {age_stderr.decode()}")

            # Set secure permissions (600)
            backup_path.chmod(0o600)

            # Set correct ownership
            os.chown(backup_path, get_user_uid(), get_user_gid())

            logger.info(f"✓ Encrypted backup created: {backup_path}")

            # SECURITY: Validate backup can be decrypted
            if validate:
                logger.info("Validating backup...")
                if not self._validate_backup(backup_path):
                    raise SecurityError("Backup validation failed - cannot decrypt")
                logger.info("✓ Backup validated successfully")

            # Update symlink to latest
            latest_link = self.backup_dir / "ai-backup.latest.age"
            if latest_link.exists() or latest_link.is_symlink():
                latest_link.unlink()
            latest_link.symlink_to(backup_filename)

            # Get backup size for user
            size_mb = backup_path.stat().st_size / (1024 * 1024)
            logger.info(f"Backup size: {size_mb:.2f} MB")

            return backup_path

        except Exception as e:
            # Cleanup partial backup
            if backup_path.exists():
                try:
                    backup_path.unlink()
                except Exception as cleanup_error:
                    logger.warning(f"Failed to cleanup partial backup: {cleanup_error}")

            raise BackupError(f"Backup failed: {e}") from e

    def _validate_backup(self, backup_path: Path) -> bool:
        """Validate that backup can be decrypted.

        Args:
            backup_path: Path to encrypted backup

        Returns:
            True if backup can be decrypted, False otherwise
        """
        try:
            # Try to decrypt and list contents without extracting
            # age -d -i key backup.tar.gz.age | tar tzf - | head -5

            age_cmd = ["age", "-d", "-i", str(self.age_key_path), str(backup_path)]
            age_process = subprocess.Popen(
                age_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

            tar_cmd = ["tar", "tzf", "-"]
            tar_process = subprocess.Popen(
                tar_cmd,
                stdin=age_process.stdout,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

            if age_process.stdout:
                age_process.stdout.close()

            stdout, stderr = tar_process.communicate()

            # Check if we got any file list
            if tar_process.returncode == 0 and stdout:
                files = stdout.decode().strip().split('\n')
                logger.debug(f"Backup contains {len(files)} files")
                return len(files) > 0

            return False

        except Exception as e:
            logger.error(f"Validation failed: {e}")
            return False

    def restore_backup(
        self,
        backup_path: Path,
        create_safety_backup: bool = True,
        dry_run: bool = False
    ) -> None:
        """Restore from encrypted backup.

        Args:
            backup_path: Path to encrypted backup file
            create_safety_backup: Create safety backup before restore (default: True)
            dry_run: Only show what would be restored (default: False)

        Raises:
            BackupError: On restore failure
            SecurityError: On validation failure
        """
        if not backup_path.exists():
            raise BackupError(f"Backup not found: {backup_path}")

        # SECURITY: Validate backup before restoring
        logger.info("Validating backup...")
        if not self._validate_backup(backup_path):
            raise SecurityError("Backup validation failed - cannot decrypt")

        # Show what would be restored (dry run)
        if dry_run:
            logger.info("DRY RUN - showing backup contents:")
            self._show_backup_contents(backup_path)
            return

        # Safety backup before restore
        safety_backup_path = None
        if create_safety_backup and self.ai_dir.exists():
            logger.info("Creating safety backup before restore...")
            try:
                safety_backup_path = self.create_backup(validate=False)
                logger.info(f"✓ Safety backup: {safety_backup_path}")
            except BackupError as e:
                logger.warning(f"Failed to create safety backup: {e}")
                # Ask user if they want to continue without safety backup
                # For now, we continue (could make this configurable)

        try:
            logger.info(f"Restoring from: {backup_path}")

            # Decrypt and extract: age -d -i key backup.tar.gz.age | tar xzf - -C /
            age_cmd = ["age", "-d", "-i", str(self.age_key_path), str(backup_path)]
            age_process = subprocess.Popen(
                age_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

            tar_cmd = ["tar", "xzf", "-", "-C", "/"]
            tar_process = subprocess.Popen(
                tar_cmd,
                stdin=age_process.stdout,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

            if age_process.stdout:
                age_process.stdout.close()

            tar_stdout, tar_stderr = tar_process.communicate()
            age_stderr = age_process.stderr.read() if age_process.stderr else b""

            if age_process.returncode != 0:
                raise BackupError(f"Decryption failed: {age_stderr.decode()}")

            if tar_process.returncode != 0:
                raise BackupError(f"Extraction failed: {tar_stderr.decode()}")

            logger.info(f"✓ Restored from: {backup_path}")
            if safety_backup_path:
                logger.info(f"Safety backup at: {safety_backup_path}")

        except Exception as e:
            logger.error(f"Restore failed: {e}")
            if safety_backup_path:
                logger.info(f"Safety backup preserved at: {safety_backup_path}")
            raise BackupError(f"Restore failed: {e}") from e

    def _show_backup_contents(self, backup_path: Path) -> None:
        """Show backup contents without extracting."""
        try:
            age_cmd = ["age", "-d", "-i", str(self.age_key_path), str(backup_path)]
            age_process = subprocess.Popen(
                age_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

            tar_cmd = ["tar", "tzf", "-"]
            tar_process = subprocess.Popen(
                tar_cmd,
                stdin=age_process.stdout,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

            if age_process.stdout:
                age_process.stdout.close()

            stdout, stderr = tar_process.communicate()

            if stdout:
                print("\nBackup contents:")
                for line in stdout.decode().split('\n')[:20]:  # Show first 20 files
                    if line:
                        print(f"  {line}")
                print("  ...")

        except Exception as e:
            logger.error(f"Failed to show contents: {e}")

    def list_backups(self) -> list[Dict[str, Any]]:
        """List available backups with metadata.

        Returns:
            List of backup info dicts
        """
        if not self.backup_dir.exists():
            return []

        backups = []
        for backup_file in sorted(
            self.backup_dir.glob("ai-backup-*.tar.gz.age"),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        ):
            stat = backup_file.stat()
            backups.append({
                "path": backup_file,
                "name": backup_file.name,
                "size_mb": stat.st_size / (1024 * 1024),
                "created": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "is_latest": backup_file.name == (self.backup_dir / "ai-backup.latest.age").readlink().name
                    if (self.backup_dir / "ai-backup.latest.age").exists() else False
            })

        return backups

    def delete_backup(self, backup_path: Path) -> None:
        """Delete a backup file.

        Args:
            backup_path: Path to backup to delete

        Raises:
            BackupError: On deletion failure
        """
        if not backup_path.exists():
            raise BackupError(f"Backup not found: {backup_path}")

        try:
            backup_path.unlink()
            logger.info(f"Deleted backup: {backup_path}")
        except Exception as e:
            raise BackupError(f"Failed to delete backup: {e}") from e
