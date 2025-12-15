#!/usr/bin/env python3
"""
Python Deployment CLI - Uses the new deployment modules
Usage: sudo python3 scripts/deploy-cli.py <command>
"""
import sys
import argparse
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ai_agents.deployment import (
    StateDetector,
    ContainerManager,
    BackupManager,
    SecretsManager,
)


def cmd_status():
    """Show deployment status using Python modules."""
    detector = StateDetector()
    state = detector.detect()

    print("=== Deployment Status (Python) ===")
    print()
    print("Infrastructure:")
    print(f"  Containers running: {'✓' if state.containers_running else '✗'}")
    print(f"  Age key exists: {'✓' if state.age_key_exists else '✗'}")
    print(f"  Python package: {'✓' if state.python_package_installed else '✗'}")
    print()

    print("Secrets Configured:")
    for agent, configured in state.secrets_configured.items():
        print(f"  {agent}: {'✓' if configured else '✗'}")
    print()

    print("State:")
    if state.is_fully_deployed:
        print("  ✓ Fully deployed")
    elif state.is_fresh_install:
        print("  ⚠ Fresh install (containers not running)")
    elif state.needs_secrets:
        print("  ⚠ Some secrets missing")
    else:
        print("  ⚠ Partial deployment")
    print()


def cmd_container_status():
    """Show container status using Python modules."""
    mgr = ContainerManager()

    print("=== Container Status (Python) ===")
    print()

    # Pod status
    print("Pod:")
    if mgr.pod_exists():
        running = mgr.is_pod_running()
        print(f"  ai-agents: {'✓ Running' if running else '✗ Stopped'}")
    else:
        print("  ai-agents: ✗ Does not exist")
    print()

    # Container status
    print("Containers:")
    containers = mgr.list_all_containers()
    if containers:
        for container in containers:
            status_icon = "✓" if container.status == "running" else "✗"
            print(f"  {status_icon} {container.name}: {container.status}")
    else:
        print("  No containers found")
    print()


def cmd_restart_containers():
    """Restart containers using Python modules."""
    mgr = ContainerManager()

    print("=== Restarting Containers (Python) ===")
    print()

    success = mgr.restart_pod()
    if success:
        print("✓ All containers restarted")
        return 0
    else:
        print("✗ Failed to restart containers")
        return 1


def cmd_stop_containers():
    """Stop containers using Python modules."""
    mgr = ContainerManager()

    print("=== Stopping Containers (Python) ===")
    print()

    success = mgr.stop_pod()
    if success:
        print("✓ All containers stopped")
        return 0
    else:
        print("✗ Failed to stop containers")
        return 1


def cmd_start_containers():
    """Start containers using Python modules."""
    mgr = ContainerManager()

    print("=== Starting Containers (Python) ===")
    print()

    success = mgr.start_pod()
    if success:
        print("✓ All containers started")
        return 0
    else:
        print("✗ Failed to start containers")
        return 1


def cmd_backup(args):
    """Create backup using Python modules."""
    mgr = BackupManager()

    print("=== Creating Backup (Python) ===")
    print()

    try:
        backup_path = mgr.create_backup(include_secrets=args.include_secrets)
        print(f"✓ Backup created: {backup_path}")
        return 0
    except Exception as e:
        print(f"✗ Backup failed: {e}")
        return 1


def cmd_list_backups():
    """List backups using Python modules."""
    mgr = BackupManager()

    print("=== Available Backups (Python) ===")
    print()

    backups = mgr.list_backups()
    if not backups:
        print("No backups found")
        return 0

    for backup in backups:
        info = mgr.get_backup_info(backup)
        if info.get("has_metadata"):
            timestamp = info.get("timestamp", "unknown")
            secrets = info.get("include_secrets", False)
            print(f"  {backup.name}")
            print(f"    Timestamp: {timestamp}")
            print(f"    Includes secrets: {'Yes' if secrets else 'No'}")
        else:
            print(f"  {backup.name} (no metadata)")
    print()


def cmd_verify_secrets():
    """Verify secrets configuration using Python modules."""
    try:
        mgr = SecretsManager()
    except Exception as e:
        print(f"✗ SecretsManager initialization failed: {e}")
        return 1

    print("=== Secrets Verification (Python) ===")
    print()

    all_ok = True
    for agent in ["claude", "grok", "gemini"]:
        exists = mgr.verify_secret_exists(agent)
        perms_ok = mgr.verify_secret_permissions(agent) if exists else False
        can_decrypt = mgr.test_decryption(agent) if exists else False

        print(f"{agent}:")
        print(f"  Exists: {'✓' if exists else '✗'}")
        if exists:
            print(f"  Permissions: {'✓ (600)' if perms_ok else '✗ (insecure)'}")
            print(f"  Decryptable: {'✓' if can_decrypt else '✗'}")

        if not (exists and perms_ok and can_decrypt):
            all_ok = False

    print()
    if all_ok:
        print("✓ All secrets configured correctly")
        return 0
    else:
        print("⚠ Some secrets have issues")
        return 1


def main():
    parser = argparse.ArgumentParser(description="Python Deployment CLI")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Status commands
    subparsers.add_parser("status", help="Show deployment status")
    subparsers.add_parser("container-status", help="Show container status")
    subparsers.add_parser("verify-secrets", help="Verify secrets configuration")

    # Container management
    subparsers.add_parser("restart", help="Restart all containers")
    subparsers.add_parser("stop", help="Stop all containers")
    subparsers.add_parser("start", help="Start all containers")

    # Backup management
    backup_parser = subparsers.add_parser("backup", help="Create backup")
    backup_parser.add_argument(
        "--no-secrets", dest="include_secrets", action="store_false", help="Exclude secrets from backup"
    )
    subparsers.add_parser("list-backups", help="List available backups")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    # Route commands
    commands = {
        "status": lambda: cmd_status(),
        "container-status": lambda: cmd_container_status(),
        "restart": lambda: cmd_restart_containers(),
        "stop": lambda: cmd_stop_containers(),
        "start": lambda: cmd_start_containers(),
        "backup": lambda: cmd_backup(args),
        "list-backups": lambda: cmd_list_backups(),
        "verify-secrets": lambda: cmd_verify_secrets(),
    }

    cmd_func = commands.get(args.command)
    if cmd_func:
        try:
            return cmd_func() or 0
        except Exception as e:
            print(f"Error: {e}")
            return 1
    else:
        print(f"Unknown command: {args.command}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
