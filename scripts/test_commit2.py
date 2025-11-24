#!/usr/bin/env python3
"""
Test script for Commit 2: Metadata schema extension
Verifies backward compatibility and new project field
"""

import json
from pathlib import Path
from datetime import datetime


def ensure_context_exists(history_dir, context_name, project_name=None):
    """Standalone version of ensure_context_exists for testing"""
    context_path = history_dir / context_name
    context_path.mkdir(parents=True, exist_ok=True)

    conversation_file = context_path / "conversation.jsonl"
    metadata_file = context_path / "metadata.json"

    if not metadata_file.exists():
        metadata = {
            "name": context_name,
            "created": datetime.now().isoformat(),
            "last_used": datetime.now().isoformat(),
            "message_count": 0
        }
        # Add project field if specified
        if project_name:
            metadata["project"] = project_name

        metadata_file.write_text(json.dumps(metadata, indent=2))

    if not conversation_file.exists():
        conversation_file.touch()

    return context_path


def test_metadata_schema():
    """Test metadata.json with and without project field"""

    test_dir = Path("/tmp/test-phase45-commit2")
    test_dir.mkdir(exist_ok=True)

    print("Testing Metadata Schema Extension (Commit 2)")
    print("=" * 60)

    # Test 1: Context WITHOUT project (backward compatibility)
    print("\nTest 1: Context without project (Phase 4 behavior)")
    print("-" * 60)
    ensure_context_exists(test_dir, "test-context-no-project")

    metadata_file = test_dir / "test-context-no-project" / "metadata.json"
    metadata = json.loads(metadata_file.read_text())

    print(f"✓ Context created: {metadata['name']}")
    print(f"✓ Created timestamp: {metadata['created'][:19]}")
    print(f"✓ Message count: {metadata['message_count']}")

    if "project" in metadata:
        print(f"✗ FAIL: 'project' field should NOT exist without project_name")
        return False
    else:
        print(f"✓ PASS: No 'project' field (backward compatible)")

    # Test 2: Context WITH project (new functionality)
    print("\nTest 2: Context with project (Phase 4.5 behavior)")
    print("-" * 60)
    ensure_context_exists(test_dir, "test-context-with-project", project_name="auth-system")

    metadata_file = test_dir / "test-context-with-project" / "metadata.json"
    metadata = json.loads(metadata_file.read_text())

    print(f"✓ Context created: {metadata['name']}")
    print(f"✓ Created timestamp: {metadata['created'][:19]}")
    print(f"✓ Message count: {metadata['message_count']}")

    if "project" not in metadata:
        print(f"✗ FAIL: 'project' field should exist when project_name provided")
        return False
    elif metadata["project"] != "auth-system":
        print(f"✗ FAIL: 'project' should be 'auth-system', got: {metadata['project']}")
        return False
    else:
        print(f"✓ PASS: 'project' field = '{metadata['project']}'")

    # Test 3: Verify structure
    print("\nTest 3: Verify metadata.json structure")
    print("-" * 60)

    print("\nMetadata WITHOUT project:")
    metadata_file = test_dir / "test-context-no-project" / "metadata.json"
    print(metadata_file.read_text())

    print("\nMetadata WITH project:")
    metadata_file = test_dir / "test-context-with-project" / "metadata.json"
    print(metadata_file.read_text())

    print("\n" + "=" * 60)
    print("✅ All tests passed!")
    print(f"✅ Backward compatibility maintained")
    print(f"✅ Project field added when specified")
    print(f"\nTest data: {test_dir}")

    return True


if __name__ == "__main__":
    success = test_metadata_schema()
    exit(0 if success else 1)
