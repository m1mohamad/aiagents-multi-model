#!/bin/bash
# Phase 2: AI Model Containers Setup
# Builds and deploys Claude, Grok, and Gemini containers
# Usage: sudo bash setup-phase2.sh

set -xe

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "ERROR: This script must be run with sudo"
    echo "Usage: sudo bash setup-phase2.sh"
    exit 1
fi

# Get actual user
ACTUAL_USER=${SUDO_USER:-$USER}
USER_UID=$(id -u $ACTUAL_USER)
USER_GID=$(id -g $ACTUAL_USER)

echo "=========================================="
echo "Phase 2: AI Model Containers Setup"
echo "=========================================="
echo "User: $ACTUAL_USER (UID: $USER_UID)"
echo ""

# Step 1: Verify Phase 1 is complete
echo "[1/7] Verifying Phase 1 setup..."
if ! podman pod exists ai-agents 2>/dev/null; then
    echo "✗ ai-agents pod not found!"
    echo "Please run setup-ai-foundation.sh first (Phase 1)"
    exit 1
fi
if [ ! -d /ai ]; then
    echo "✗ /ai directory not found!"
    echo "Please run setup-ai-foundation.sh first (Phase 1)"
    exit 1
fi
echo "✓ Phase 1 verified"
echo ""

# Step 2: Create Dockerfiles
echo "[2/7] Creating Dockerfiles..."
BUILD_DIR="/home/aiagent/ai-setup"
mkdir -p "$BUILD_DIR"

# Dockerfile for Claude
cat > "$BUILD_DIR/Dockerfile.claude" << 'EOF'
FROM localhost/ai-base:secure

USER root
RUN pip3 install anthropic python-dotenv --no-cache-dir

USER agent
WORKDIR /home/agent
EOF

# Dockerfile for Grok
cat > "$BUILD_DIR/Dockerfile.grok" << 'EOF'
FROM localhost/ai-base:secure

USER root
RUN pip3 install requests python-dotenv --no-cache-dir

USER agent
WORKDIR /home/agent
EOF

# Dockerfile for Gemini
cat > "$BUILD_DIR/Dockerfile.gemini" << 'EOF'
FROM localhost/ai-base:secure

USER root
RUN pip3 install google-generativeai python-dotenv --no-cache-dir

USER agent
WORKDIR /home/agent
EOF

echo "✓ Dockerfiles created"
echo ""

# Step 3: Build images
echo "[3/7] Building container images (this may take 2-4 minutes)..."
echo ""
echo "Building ai-claude:latest..."
podman build -t ai-claude:latest -f "$BUILD_DIR/Dockerfile.claude" "$BUILD_DIR"
echo ""
echo "Building ai-grok:latest..."
podman build -t ai-grok:latest -f "$BUILD_DIR/Dockerfile.grok" "$BUILD_DIR"
echo ""
echo "Building ai-gemini:latest..."
podman build -t ai-gemini:latest -f "$BUILD_DIR/Dockerfile.gemini" "$BUILD_DIR"
echo ""
echo "✓ All images built"
echo ""

# Step 4: Stop and remove test container
echo "[4/7] Cleaning up test container..."
podman stop test-agent 2>/dev/null || true
podman rm test-agent 2>/dev/null || true
echo "✓ Test container removed"
echo ""

# Step 5: Launch Claude container
echo "[5/7] Launching AI containers..."
podman run -d --pod ai-agents --name claude-agent \
  --user $USER_UID:$USER_GID \
  -v /ai/claude:/ai/claude:rw \
  -v /ai/shared:/ai/shared:ro \
  -v /ai/logs:/ai/logs:rw \
  ai-claude:latest sleep infinity
echo "  ✓ claude-agent launched"

# Launch Grok container
podman run -d --pod ai-agents --name grok-agent \
  --user $USER_UID:$USER_GID \
  -v /ai/grok:/ai/grok:rw \
  -v /ai/shared:/ai/shared:ro \
  -v /ai/logs:/ai/logs:rw \
  ai-grok:latest sleep infinity
echo "  ✓ grok-agent launched"

# Launch Gemini container
podman run -d --pod ai-agents --name gemini-agent \
  --user $USER_UID:$USER_GID \
  -v /ai/gemini:/ai/gemini:rw \
  -v /ai/shared:/ai/shared:ro \
  -v /ai/logs:/ai/logs:rw \
  ai-gemini:latest sleep infinity
echo "  ✓ gemini-agent launched"
echo ""

# Step 6: Verify containers
echo "[6/7] Verifying container SDKs..."
sleep 2

if podman exec claude-agent python3 -c "import anthropic" 2>/dev/null; then
    echo "  ✓ Claude SDK installed"
else
    echo "  ✗ Claude SDK verification failed"
fi

if podman exec grok-agent python3 -c "import requests" 2>/dev/null; then
    echo "  ✓ Grok tools installed"
else
    echo "  ✗ Grok tools verification failed"
fi

if podman exec gemini-agent python3 -c "import google.generativeai" 2>/dev/null; then
    echo "  ✓ Gemini SDK installed"
else
    echo "  ✗ Gemini SDK verification failed"
fi
echo ""

# Step 7: Verify file access
echo "[7/7] Verifying file access..."
if podman exec claude-agent bash -c "echo 'claude-test' > /ai/logs/claude-test.log" 2>/dev/null; then
    echo "  ✓ Claude can write to logs"
else
    echo "  ✗ Claude file access failed"
fi

if podman exec grok-agent bash -c "echo 'grok-test' > /ai/logs/grok-test.log" 2>/dev/null; then
    echo "  ✓ Grok can write to logs"
else
    echo "  ✗ Grok file access failed"
fi

if podman exec gemini-agent bash -c "echo 'gemini-test' > /ai/logs/gemini-test.log" 2>/dev/null; then
    echo "  ✓ Gemini can write to logs"
else
    echo "  ✗ Gemini file access failed"
fi
echo ""

echo "=========================================="
echo "Phase 2 Complete!"
echo "=========================================="
echo ""
echo "Container Status:"
podman ps --pod --filter "pod=ai-agents"
echo ""
echo "Images Built:"
podman images | grep "ai-"
echo ""
echo "Next Steps:"
echo "1. Test container access:"
echo "   sudo podman exec -it claude-agent /bin/bash"
echo "   sudo podman exec -it grok-agent /bin/bash"
echo "   sudo podman exec -it gemini-agent /bin/bash"
echo ""
echo "2. Proceed to Phase 3: Authentication & Configuration"
echo ""
echo "Quick Test Commands:"
echo "  Claude:  sudo podman exec claude-agent python3 -c 'import anthropic; print(\"Ready\")'"
echo "  Grok:    sudo podman exec grok-agent python3 -c 'import requests; print(\"Ready\")'"
echo "  Gemini:  sudo podman exec gemini-agent python3 -c 'import google.generativeai; print(\"Ready\")'"
echo ""
