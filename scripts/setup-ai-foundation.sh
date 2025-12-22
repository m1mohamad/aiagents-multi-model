#!/bin/bash
# AI Foundation Setup Script
# Creates secure multi-model AI infrastructure using rootful Podman
# Usage: sudo bash setup-ai-foundation.sh

set -e  # Exit on any error

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "ERROR: This script must be run with sudo"
    echo "Usage: sudo bash setup-ai-foundation.sh"
    exit 1
fi

# Get the actual user (not root when using sudo)
ACTUAL_USER=${SUDO_USER:-$USER}
USER_UID=$(id -u $ACTUAL_USER)
USER_GID=$(id -g $ACTUAL_USER)

echo "=========================================="
echo "AI Foundation Setup"
echo "=========================================="
echo "User: $ACTUAL_USER (UID: $USER_UID)"
echo ""

# Step 1: Clean up existing infrastructure
echo "[1/8] Cleaning up existing infrastructure..."
podman pod rm -f ai-agents 2>/dev/null || true
podman rm -f test-agent 2>/dev/null || true
sudo -u $ACTUAL_USER podman pod rm -f ai-agents 2>/dev/null || true
sudo -u $ACTUAL_USER podman rm -f test-agent 2>/dev/null || true
echo "✓ Cleanup complete"
echo ""

# Step 2: Create aiagent group and add user
echo "[2/8] Setting up aiagent group..."
if ! getent group aiagent >/dev/null 2>&1; then
    groupadd aiagent
    echo "✓ Created aiagent group"
else
    echo "✓ aiagent group exists"
fi

if ! getent group aiagent | grep -q "\b$ACTUAL_USER\b"; then
    usermod -aG aiagent $ACTUAL_USER
    echo "✓ Added $ACTUAL_USER to aiagent group"
    echo "⚠️  You must logout/login for group membership to take effect!"
else
    echo "✓ $ACTUAL_USER already in aiagent group"
fi
echo ""

# Step 3: Create aiagent service user
echo "[3/8] Creating aiagent service user..."
if ! id aiagent >/dev/null 2>&1; then
    useradd -r -s /usr/sbin/nologin -m -d /home/aiagent aiagent
    echo "✓ Created aiagent user"
else
    echo "✓ aiagent user exists"
fi
echo ""

# Step 4: Create directory structure
echo "[4/8] Creating /ai directory structure..."
mkdir -p /ai/{shared/references,claude/{context,history,workspace},grok/{context,history},gemini/{context,history},groq/{context,history},huggingface/{context,history},logs}
chown -R $ACTUAL_USER:aiagent /ai
chmod 750 /ai
chmod 755 /ai/shared
chmod 700 /ai/{claude,grok,gemini,groq,huggingface}
chmod 733 /ai/logs
echo "✓ Directory structure created"
echo ""

# Step 5: Build base image
echo "[5/8] Building base container image..."
BUILD_DIR=$(mktemp -d)

cat > "$BUILD_DIR/Dockerfile.base" << 'EOF'
FROM ubuntu:22.04

RUN apt-get update && apt-get install -y \
    python3-pip python3-venv curl jq \
    --no-install-recommends && \
    rm -rf /var/lib/apt/lists/*

RUN useradd -u 1001 -m agent

USER agent
WORKDIR /home/agent
EOF

podman build -t ai-base:secure -f "$BUILD_DIR/Dockerfile.base" "$BUILD_DIR" >/dev/null 2>&1
rm -rf "$BUILD_DIR"
echo "✓ Base image built: ai-base:secure"
echo ""

# Step 6: Create pod with network isolation
echo "[6/8] Creating ai-agents pod..."
podman pod create --name ai-agents --network slirp4netns >/dev/null 2>&1
echo "✓ Pod created: ai-agents"
echo ""

# Step 7: Launch test container
echo "[7/8] Launching test container..."
podman run -d --pod ai-agents --name test-agent \
  --user $USER_UID:$USER_GID \
  -v /ai:/ai:rw \
  ai-base:secure sleep infinity >/dev/null 2>&1
echo "✓ Test container launched"
echo ""

# Step 8: Validate setup
echo "[8/8] Validating setup..."
sleep 2

# Test container access
if podman exec test-agent bash -c "echo 'validation' > /ai/logs/setup-test.log" 2>/dev/null; then
    if [ -f /ai/logs/setup-test.log ]; then
        echo "✓ Container can write to /ai/logs"
    else
        echo "✗ Container write test failed"
        exit 1
    fi
else
    echo "✗ Container exec failed"
    exit 1
fi

echo ""
echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo ""
echo "Current Status:"
podman pod ps
echo ""
podman ps --pod
echo ""
echo "Next Steps:"
echo "1. If this is your first time: logout/login to activate group membership"
echo "2. Verify with: groups | grep aiagent"
echo "3. Test access: sudo podman exec test-agent ls -la /ai"
echo "4. Proceed to Phase 2: Build model-specific containers"
echo ""
echo "Quick Commands:"
echo "  Start:  sudo podman pod start ai-agents"
echo "  Stop:   sudo podman pod stop ai-agents"
echo "  Shell:  sudo podman exec -it test-agent /bin/bash"
echo ""
