#!/bin/bash
set -e

ACTUAL_USER=${SUDO_USER:-$USER}
PUBLIC_KEY=$(sudo -u $ACTUAL_USER grep "public key:" ~$ACTUAL_USER/.age-key.txt 2>/dev/null | awk '{print $NF}')

if [ -z "$PUBLIC_KEY" ]; then
    echo "Error: Age key not found. Run 'make deploy' first."
    exit 1
fi

echo "=========================================="
echo "AI Agent Secrets Configuration"
echo "=========================================="
echo ""
echo "Get your keys from:"
echo "  Claude:  https://claude.ai (Cookie: sessionKey)"
echo "  Grok:    https://console.x.ai (API Keys)"
echo "  Gemini:  https://aistudio.google.com/app/apikey"
echo ""

configure_agent() {
    local agent=$1
    local prompt=$2

    read -p "$prompt (or Enter to skip): " KEY
    if [ ! -z "$KEY" ]; then
        echo "$KEY" | age -r $PUBLIC_KEY -o /ai/$agent/context/.secrets.age
        chmod 600 /ai/$agent/context/.secrets.age
        chown $ACTUAL_USER:aiagent /ai/$agent/context/.secrets.age
        echo "  ✓ $agent configured"
        return 0
    else
        echo "  ⊘ $agent skipped"
        return 1
    fi
}

configure_agent "claude" "Claude API key"
echo ""
configure_agent "grok" "Grok API key"
echo ""
configure_agent "gemini" "Gemini API key"

echo ""
echo "=========================================="
echo "Done! Test with: make test"
echo "=========================================="
