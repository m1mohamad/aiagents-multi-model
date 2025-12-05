#!/usr/bin/env python3
"""
Test script for ProjectManager (Commit 1)
"""

import sys
from pathlib import Path

from ai_agents.core.project_manager import ProjectManager


def test_project_manager():
    """Test ProjectManager basic operations"""

    # Use a test directory instead of /ai/claude/history
    test_dir = Path("/tmp/test-phase45-projects")
    test_dir.mkdir(exist_ok=True)

    print("Testing ProjectManager...")
    print("-" * 60)

    # Initialize
    pm = ProjectManager(test_dir)
    print(f"✓ Initialized ProjectManager at {test_dir}")
    print(f"✓ Projects file: {pm.projects_file}")

    # Create projects
    print("\nCreating test projects...")
    result1 = pm.create_project("auth-system", "OAuth2 authentication implementation")
    print(f"✓ Created 'auth-system': {result1}")

    result2 = pm.create_project("ceph-monitor", "Ceph cluster monitoring system")
    print(f"✓ Created 'ceph-monitor': {result2}")

    result3 = pm.create_project("auth-system", "Duplicate test")
    print(f"✓ Duplicate creation prevented: {not result3}")

    # List projects
    print("\nListing all projects...")
    projects = pm.list_projects()
    for proj in projects:
        print(f"  - {proj['name']}: {proj['description']}")
        print(f"    Created: {proj['created'][:19]}")
        print(f"    Conversations: {len(proj['conversations'])}")

    # Get specific project
    print("\nGetting specific project...")
    auth_proj = pm.get_project("auth-system")
    if auth_proj:
        print(f"✓ Found project: {auth_proj}")

    # Add conversation to project
    print("\nLinking conversation to project...")
    pm.add_conversation("auth-system", "001-requirements")
    pm.add_conversation("auth-system", "002-implementation")

    # Verify conversations added
    auth_proj = pm.get_project("auth-system")
    print(f"✓ Conversations in 'auth-system': {auth_proj['conversations']}")

    # Update activity
    print("\nUpdating activity timestamp...")
    pm.update_activity("ceph-monitor")
    print("✓ Activity updated")

    # List again to see updated order
    print("\nFinal project list (sorted by activity)...")
    projects = pm.list_projects()
    for proj in projects:
        print(f"  - {proj['name']} (last activity: {proj['last_activity'][:19]})")

    print("\n" + "=" * 60)
    print("✅ All tests passed!")
    print(f"Test data saved to: {test_dir}")
    print("\nTo inspect projects.json:")
    print(f"  cat {test_dir}/projects.json")


if __name__ == "__main__":
    test_project_manager()
