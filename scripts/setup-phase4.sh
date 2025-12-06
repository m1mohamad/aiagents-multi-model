#!/bin/bash
# Phase 4: Full API & Conversation History Setup
# Installs complete API implementations with conversation persistence
# Usage: sudo bash setup-phase4.sh

set -e

if [ "$EUID" -ne 0 ]; then
    echo "ERROR: This script must be run with sudo"
    echo "Usage: sudo bash setup-phase4.sh"
    exit 1
fi

ACTUAL_USER=${SUDO_USER:-$USER}
USER_HOME=$(eval echo ~$ACTUAL_USER)
USER_UID=$(id -u $ACTUAL_USER)
USER_GID=$(id -g $ACTUAL_USER)
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

echo "=========================================="
echo "Phase 4: Full API & Conversation History"
echo "=========================================="
echo "User: $ACTUAL_USER"
echo ""

# Step 1: Verify prerequisites
echo "[1/6] Verifying prerequisites..."

# Check Phase 3 is complete
if ! podman ps --filter "name=claude-agent" --format "{{.Names}}" | grep -q "claude-agent"; then
    echo "✗ claude-agent not running. Please complete Phase 3 first."
    exit 1
fi

if ! podman ps --filter "name=grok-agent" --format "{{.Names}}" | grep -q "grok-agent"; then
    echo "✗ grok-agent not running. Please complete Phase 3 first."
    exit 1
fi

if ! podman ps --filter "name=gemini-agent" --format "{{.Names}}" | grep -q "gemini-agent"; then
    echo "✗ gemini-agent not running. Please complete Phase 3 first."
    exit 1
fi

echo "✓ All containers running"
echo ""

# Step 2: Create history directories
echo "[2/6] Creating conversation history directories..."
mkdir -p /ai/claude/history/default
mkdir -p /ai/grok/history/default
mkdir -p /ai/gemini/history/default
mkdir -p /ai/shared/agent-messages

chown -R $ACTUAL_USER:aiagent /ai/*/history
chown -R $ACTUAL_USER:aiagent /ai/shared/agent-messages
chmod 750 /ai/*/history
chmod 750 /ai/*/history/default
chmod 755 /ai/shared/agent-messages

echo "✓ History directories created"
echo ""

# Step 3: Install Python dependencies in containers
echo "[3/6] Installing additional Python dependencies..."

echo "  Installing in claude-agent..."
podman exec -u root claude-agent pip3 install anthropic --upgrade --no-cache-dir >/dev/null 2>&1 || true

echo "  Installing in grok-agent..."
podman exec -u root grok-agent pip3 install requests --upgrade --no-cache-dir >/dev/null 2>&1 || true

echo "  Installing in gemini-agent..."
podman exec -u root gemini-agent pip3 install google-generativeai --upgrade --no-cache-dir >/dev/null 2>&1 || true

echo "✓ Dependencies updated"
echo ""

# Step 4: Copy API implementations to containers
echo "[4/6] Installing full API implementations..."

# Copy Python scripts to containers
for script in claude-api.py grok-api.py gemini-api.py; do
    if [ -f "$SCRIPT_DIR/$script" ]; then
        agent_name=$(echo $script | cut -d'-' -f1)

        podman cp "$SCRIPT_DIR/$script" ${agent_name}-agent:/home/agent/${script}
        podman exec -u root ${agent_name}-agent chmod +x /home/agent/${script}
        podman exec -u root ${agent_name}-agent chown $USER_UID:$USER_GID /home/agent/${script}

        echo "  ✓ Installed $script in ${agent_name}-agent"
    else
        echo "  ✗ Warning: $script not found in $SCRIPT_DIR"
    fi
done

echo ""

# Step 5: Create new CLI wrapper scripts
echo "[5/6] Creating enhanced CLI wrappers..."

# Claude wrapper
cat > /tmp/claude-chat << 'EOFCLAUDE'
#!/bin/bash
cd /home/agent
exec python3 /home/agent/claude-api.py "$@"
EOFCLAUDE

# Grok wrapper
cat > /tmp/grok-chat << 'EOFGROK'
#!/bin/bash
cd /home/agent
exec python3 /home/agent/grok-api.py "$@"
EOFGROK

# Gemini wrapper
cat > /tmp/gemini-chat << 'EOFGEMINI'
#!/bin/bash
cd /home/agent
exec python3 /home/agent/gemini-api.py "$@"
EOFGEMINI

# Install wrappers in containers
for agent in claude grok gemini; do
    podman cp /tmp/${agent}-chat ${agent}-agent:/home/agent/${agent}-chat
    podman exec -u root ${agent}-agent chmod +x /home/agent/${agent}-chat
    podman exec -u root ${agent}-agent chown $USER_UID:$USER_GID /home/agent/${agent}-chat
    echo "  ✓ Installed ${agent}-chat wrapper"
done

rm -f /tmp/claude-chat /tmp/grok-chat /tmp/gemini-chat
echo ""

# Step 6: Create host-side convenience scripts
echo "[6/6] Creating host-side CLI helpers..."

mkdir -p /usr/local/bin

# Claude helper
cat > /usr/local/bin/ai-claude << 'EOFCLAUDEHOST'
#!/bin/bash
sudo podman exec -i claude-agent /home/agent/claude-chat "$@"
EOFCLAUDEHOST

# Grok helper
cat > /usr/local/bin/ai-grok << 'EOFGROKHOST'
#!/bin/bash
sudo podman exec -i grok-agent /home/agent/grok-chat "$@"
EOFGROKHOST

# Gemini helper
cat > /usr/local/bin/ai-gemini << 'EOFGEMINIHOST'
#!/bin/bash
sudo podman exec -i gemini-agent /home/agent/gemini-chat "$@"
EOFGEMINIHOST

chmod +x /usr/local/bin/ai-claude /usr/local/bin/ai-grok /usr/local/bin/ai-gemini
chown $ACTUAL_USER:$ACTUAL_USER /usr/local/bin/ai-claude /usr/local/bin/ai-grok /usr/local/bin/ai-gemini

echo "  ✓ Host CLI helpers installed (/usr/local/bin/ai-claude, ai-grok, ai-gemini)"
echo ""

# Test installations
echo "=========================================="
echo "Phase 4 Complete!"
echo "=========================================="
echo ""

echo "Available Commands:"
echo ""
echo "  Host (from anywhere):"
echo "    ai-claude \"message\"                    # Use default context"
echo "    ai-claude --context project \"message\"  # Use specific context"
echo "    ai-claude --list                        # List all contexts"
echo "    ai-claude --switch project-auth         # Switch active context"
echo ""
echo "  Same for: ai-grok and ai-gemini"
echo ""
echo "  Container (exec into container first):"
echo "    sudo podman exec -it claude-agent bash"
echo "    ./claude-chat \"message\""
echo ""

echo "Testing API installations..."
echo ""

# Test Claude
if [ -f /ai/claude/context/.secrets.age ]; then
    echo -n "  Claude API: "
    if podman exec claude-agent python3 -c "from anthropic import Anthropic; print('✓ Ready')" 2>/dev/null; then
        echo "✓ Ready"
    else
        echo "✗ Failed"
    fi
else
    echo "  Claude API: ⚠ No credentials configured"
fi

# Test Grok
if [ -f /ai/grok/context/.secrets.age ]; then
    echo -n "  Grok API: "
    if podman exec grok-agent python3 -c "import requests; print('✓ Ready')" 2>/dev/null; then
        echo "✓ Ready"
    else
        echo "✗ Failed"
    fi
else
    echo "  Grok API: ⚠ No credentials configured"
fi

# Test Gemini
if [ -f /ai/gemini/context/.secrets.age ]; then
    echo -n "  Gemini API: "
    if podman exec gemini-agent python3 -c "import google.generativeai; print('✓ Ready')" 2>/dev/null; then
        echo "✓ Ready"
    else
        echo "✗ Failed"
    fi
else
    echo "  Gemini API: ⚠ No credentials configured"
fi

echo ""
echo "Quick Test (if credentials configured):"
echo "  ai-gemini \"What is 2+2?\""
echo "  ai-claude --context test \"Explain quantum computing briefly\""
echo "  ai-grok \"What's trending in AI?\""
echo ""
echo "Documentation: docs/phase4-conversations.md"
echo ""
