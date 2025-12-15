#!/bin/bash
# Emergency fix: Safe update script
# Preserves secrets and data while updating code

set -e

if [ "$EUID" -ne 0 ]; then
    echo "ERROR: Must run with sudo"
    exit 1
fi

ACTUAL_USER=${SUDO_USER:-$USER}

echo "========================================"
echo "AI Agents - Safe Update"
echo "========================================"
echo ""

# Check if setup exists
if ! podman pod exists ai-agents 2>/dev/null; then
    echo "✗ No existing deployment found"
    echo "Run 'make deploy' for first-time setup"
    exit 1
fi

echo "✓ Found existing deployment"
echo ""

# Check for secrets
echo "[1/5] Checking for secrets..."
SECRET_COUNT=0
for agent in claude grok gemini; do
    if [ -f "/ai/$agent/context/.secrets.age" ]; then
        echo "  ✓ $agent secrets found"
        ((SECRET_COUNT++))
    else
        echo "  ⚠️  $agent secrets MISSING"
    fi
done

if [ $SECRET_COUNT -eq 0 ]; then
    echo ""
    echo "⚠️  WARNING: No secrets found!"
    echo "This might be a fresh install. Continue anyway?"
    read -p "Continue? [y/N] " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Backup secrets
echo ""
echo "[2/5] Backing up secrets..."
BACKUP_DIR="/tmp/ai-secrets-backup-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BACKUP_DIR"

for agent in claude grok gemini; do
    if [ -f "/ai/$agent/context/.secrets.age" ]; then
        cp "/ai/$agent/context/.secrets.age" "$BACKUP_DIR/$agent.secrets.age"
        echo "  ✓ Backed up $agent secret"
    fi
done

echo "✓ Secrets backed up to: $BACKUP_DIR"

# Update container code
echo ""
echo "[3/5] Updating container code..."

# Copy project_manager.py to all containers
if [ -f "src/ai_agents/core/project_manager.py" ]; then
    for agent in claude grok gemini; do
        if podman container exists ${agent}-agent 2>/dev/null; then
            podman cp src/ai_agents/core/project_manager.py ${agent}-agent:/home/agent/
            podman exec -u root ${agent}-agent chown 1002:1002 /home/agent/project_manager.py
            echo "  ✓ Updated ${agent}-agent"
        fi
    done
else
    echo "  ⚠️  project_manager.py not found, skipping update"
fi

# Restart containers to pick up changes
echo ""
echo "[4/5] Restarting containers..."
podman pod restart ai-agents
sleep 3

# Verify secrets still exist
echo ""
echo "[5/5] Verifying secrets..."
MISSING=0
for agent in claude grok gemini; do
    if [ -f "/ai/$agent/context/.secrets.age" ]; then
        echo "  ✓ $agent secrets OK"
    else
        echo "  ✗ $agent secrets MISSING"
        ((MISSING++))
    fi
done

if [ $MISSING -gt 0 ]; then
    echo ""
    echo "⚠️  Some secrets are missing!"
    echo "Restore from backup: $BACKUP_DIR"
fi

echo ""
echo "✓ Update complete!"
echo ""
echo "Test with: make test"
echo "Backup location: $BACKUP_DIR"
