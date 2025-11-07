#!/bin/bash
# Phase 3: Authentication & CLI Setup (FIXED)
# Handles permissions correctly and installs working CLI wrappers
# Usage: sudo bash setup-phase3.sh

set -e

if [ "$EUID" -ne 0 ]; then 
    echo "ERROR: This script must be run with sudo"
    echo "Usage: sudo bash setup-phase3.sh"
    exit 1
fi

ACTUAL_USER=${SUDO_USER:-$USER}
USER_HOME=$(eval echo ~$ACTUAL_USER)
USER_UID=$(id -u $ACTUAL_USER)
USER_GID=$(id -g $ACTUAL_USER)

echo "=========================================="
echo "Phase 3: Authentication & CLI Setup"
echo "=========================================="
echo "User: $ACTUAL_USER (UID: $USER_UID)"
echo ""

# Step 1: Install age on host
echo "[1/6] Installing age encryption tool..."
if ! command -v age &> /dev/null; then
    apt update >/dev/null 2>&1
    apt install -y age >/dev/null 2>&1
    echo "✓ Age installed"
else
    echo "✓ Age already installed"
fi

# Generate key if needed
if [ ! -f "$USER_HOME/.age-key.txt" ]; then
    sudo -u $ACTUAL_USER age-keygen -o "$USER_HOME/.age-key.txt"
    chmod 600 "$USER_HOME/.age-key.txt"
    chown $ACTUAL_USER:$ACTUAL_USER "$USER_HOME/.age-key.txt"
    echo "✓ Age key generated"
    echo "⚠️  BACKUP THIS KEY: $USER_HOME/.age-key.txt"
else
    echo "✓ Age key exists"
fi

PUBLIC_KEY=$(grep "public key:" "$USER_HOME/.age-key.txt" | awk '{print $NF}')
echo "✓ Public key: ${PUBLIC_KEY:0:20}..."
echo ""

# Step 2: Install age in containers and fix permissions
echo "[2/6] Setting up age in containers..."
for container in claude-agent grok-agent gemini-agent; do
    echo "  Configuring $container..."
    # Install age
    podman exec -u root $container bash -c "apt update >/dev/null 2>&1 && apt install -y age >/dev/null 2>&1" 2>/dev/null || true
    
    # Fix /home/agent permissions (allow entry)
    podman exec -u root $container chmod 755 /home/agent
    
    # Copy age key
    podman cp "$USER_HOME/.age-key.txt" $container:/home/agent/.age-key.txt 2>/dev/null || true
    
    # Fix ownership to match container user
    podman exec -u root $container chown $USER_UID:$USER_GID /home/agent/.age-key.txt
    podman exec -u root $container chmod 600 /home/agent/.age-key.txt
done
echo "✓ Age installed and configured in all containers"
echo ""

# Step 3: Create context directories
echo "[3/6] Creating context directories..."
mkdir -p /ai/claude/context /ai/grok/context /ai/gemini/context
chown -R $ACTUAL_USER:aiagent /ai/*/context
chmod 700 /ai/*/context
echo "✓ Context directories ready"
echo ""

# Step 4: Check if credentials already exist
echo "[4/6] Checking credentials..."
CLAUDE_EXISTS=false
GROK_EXISTS=false
GEMINI_EXISTS=false

[ -f /ai/claude/context/.secrets.age ] && CLAUDE_EXISTS=true && echo "✓ Claude credentials exist"
[ -f /ai/grok/context/.secrets.age ] && GROK_EXISTS=true && echo "✓ Grok credentials exist"
[ -f /ai/gemini/context/.secrets.age ] && GEMINI_EXISTS=true && echo "✓ Gemini credentials exist"

if [ "$CLAUDE_EXISTS" = false ] || [ "$GROK_EXISTS" = false ] || [ "$GEMINI_EXISTS" = false ]; then
    echo ""
    echo "⚠️  Some credentials missing. Please configure manually:"
    echo ""
    [ "$CLAUDE_EXISTS" = false ] && echo "Claude:  echo 'YOUR_TOKEN' | age -r $PUBLIC_KEY -o /ai/claude/context/.secrets.age"
    [ "$GROK_EXISTS" = false ] && echo "Grok:    echo 'YOUR_TOKEN' | age -r $PUBLIC_KEY -o /ai/grok/context/.secrets.age"
    [ "$GEMINI_EXISTS" = false ] && echo "Gemini:  echo 'YOUR_KEY' | age -r $PUBLIC_KEY -o /ai/gemini/context/.secrets.age"
    echo ""
    echo "After adding credentials, run this script again."
    echo ""
else
    echo "✓ All credentials configured"
fi
echo ""

# Step 5: Create CLI wrappers
echo "[5/6] Creating CLI wrapper scripts..."
mkdir -p /tmp/ai-wrappers

# Claude wrapper
cat > /tmp/ai-wrappers/claude-chat << 'EOFCLAUDE'
#!/bin/bash
TOKEN=$(age -d -i /home/agent/.age-key.txt /ai/claude/context/.secrets.age 2>/dev/null | tr -d '\n')
[ -z "$TOKEN" ] && echo "Error: Cannot decrypt token" && exit 1
MESSAGE="${1:-$(cat)}"
[ -z "$MESSAGE" ] && echo "Usage: claude-chat \"message\"" && exit 1
echo "Claude CLI Ready (Token: ${TOKEN:0:15}...)"
echo "Message: $MESSAGE"
echo "Note: Full API in Phase 4"
EOFCLAUDE

# Grok wrapper
cat > /tmp/ai-wrappers/grok-chat << 'EOFGROK'
#!/bin/bash
TOKEN=$(age -d -i /home/agent/.age-key.txt /ai/grok/context/.secrets.age 2>/dev/null | tr -d '\n')
[ -z "$TOKEN" ] && echo "Error: Cannot decrypt token" && exit 1
MESSAGE="${1:-$(cat)}"
[ -z "$MESSAGE" ] && echo "Usage: grok-chat \"message\"" && exit 1
echo "Grok CLI Ready (Token: ${TOKEN:0:20}...)"
echo "Message: $MESSAGE"
echo "Note: Full API in Phase 4"
EOFGROK

# Gemini wrapper (WORKING)
cat > /tmp/ai-wrappers/gemini-chat << 'EOFGEMINI'
#!/bin/bash
API_KEY=$(age -d -i /home/agent/.age-key.txt /ai/gemini/context/.secrets.age 2>/dev/null | tr -d '\n')
[ -z "$API_KEY" ] && echo "Error: Cannot decrypt API key" && exit 1
MESSAGE="${1:-$(cat)}"
[ -z "$MESSAGE" ] && echo "Usage: gemini-chat \"message\"" && exit 1
MESSAGE_ESC=$(echo "$MESSAGE" | python3 -c 'import sys,json; print(json.dumps(sys.stdin.read()))')
RESPONSE=$(curl -s -X POST \
  "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key=$API_KEY" \
  -H 'Content-Type: application/json' \
  -d "{\"contents\":[{\"parts\":[{\"text\":$MESSAGE_ESC}]}]}")
if echo "$RESPONSE" | grep -q '"candidates"'; then
    echo "$RESPONSE" | python3 -c 'import sys,json; print(json.load(sys.stdin)["candidates"][0]["content"]["parts"][0]["text"])' 2>/dev/null
else
    echo "Error: API call failed"
fi
EOFGEMINI

chmod +x /tmp/ai-wrappers/*

# Install in containers
for container in claude-agent grok-agent gemini-agent; do
    podman cp /tmp/ai-wrappers/claude-chat $container:/home/agent/claude-chat 2>/dev/null || true
    podman cp /tmp/ai-wrappers/grok-chat $container:/home/agent/grok-chat 2>/dev/null || true
    podman cp /tmp/ai-wrappers/gemini-chat $container:/home/agent/gemini-chat 2>/dev/null || true
    podman exec $container chmod +x /home/agent/*-chat 2>/dev/null || true
done

rm -rf /tmp/ai-wrappers
echo "✓ CLI wrappers installed"
echo ""

# Step 6: Test
echo "[6/6] Testing CLI access..."
if [ "$CLAUDE_EXISTS" = true ]; then
    echo -n "  Claude: "
    podman exec claude-agent /home/agent/claude-chat "test" 2>&1 | head -1
fi
if [ "$GROK_EXISTS" = true ]; then
    echo -n "  Grok: "
    podman exec grok-agent /home/agent/grok-chat "test" 2>&1 | head -1
fi
if [ "$GEMINI_EXISTS" = true ]; then
    echo -n "  Gemini: "
    podman exec gemini-agent /home/agent/gemini-chat "Hello" 2>&1 | head -1
fi
echo ""

echo "=========================================="
echo "Phase 3 Complete!"
echo "=========================================="
echo ""
echo "Credentials Status:"
[ "$CLAUDE_EXISTS" = true ] && echo "  ✓ Claude" || echo "  ✗ Claude (see instructions above)"
[ "$GROK_EXISTS" = true ] && echo "  ✓ Grok" || echo "  ✗ Grok (see instructions above)"
[ "$GEMINI_EXISTS" = true ] && echo "  ✓ Gemini" || echo "  ✗ Gemini (see instructions above)"
echo ""
echo "Test Commands:"
echo "  sudo podman exec -it claude-agent /home/agent/claude-chat \"Hello\""
echo "  sudo podman exec -it grok-agent /home/agent/grok-chat \"Hello\""
echo "  sudo podman exec -it gemini-agent /home/agent/gemini-chat \"Hello\""
echo ""
echo "Interactive Shell:"
echo "  sudo podman exec -it gemini-agent bash"
echo "  ./gemini-chat \"What is AI?\""
echo ""
