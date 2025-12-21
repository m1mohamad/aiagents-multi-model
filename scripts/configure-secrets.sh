#!/bin/bash
set -e

ACTUAL_USER=${SUDO_USER:-$USER}
AGE_KEY_PATH="/home/$ACTUAL_USER/.age-key.txt"

if [ ! -f "$AGE_KEY_PATH" ]; then
    echo "Error: Age key not found at $AGE_KEY_PATH"
    echo "Run 'make deploy' to generate it."
    exit 1
fi

PUBLIC_KEY=$(grep "public key:" "$AGE_KEY_PATH" | awk '{print $NF}')

echo "=========================================="
echo "AI Agent Secrets Configuration"
echo "=========================================="
echo ""
echo "Get your keys from:"
echo "  Claude:       https://claude.ai (Cookie: sessionKey)"
echo "  Grok:         https://console.x.ai (API Keys)"
echo "  Gemini:       https://aistudio.google.com/app/apikey"
echo "  Groq:         https://console.groq.com/keys (FREE - ultra-fast)"
echo "  HuggingFace:  https://huggingface.co/settings/tokens (FREE)"
echo ""

check_secret_exists() {
    local agent=$1
    test -f "/ai/$agent/context/.secrets.age"
}

configure_agent() {
    local agent=$1
    local prompt=$2

    # Check if secret already exists
    if check_secret_exists "$agent"; then
        echo "  ℹ $agent: Secret already configured"
        read -p "  Re-configure? (y/N): " reconfigure
        if [ "$reconfigure" != "y" ] && [ "$reconfigure" != "Y" ]; then
            echo "  ✓ $agent: Keeping existing secret"
            return 0
        fi
    fi

    # Prompt for new key
    read -p "$prompt (or Enter to skip): " KEY
    if [ ! -z "$KEY" ]; then
        echo "$KEY" | age -r $PUBLIC_KEY -o /ai/$agent/context/.secrets.age
        chmod 600 /ai/$agent/context/.secrets.age
        chown $ACTUAL_USER:aiagent /ai/$agent/context/.secrets.age
        echo "  ✓ $agent configured"
        return 0
    else
        if check_secret_exists "$agent"; then
            echo "  ✓ $agent: Keeping existing secret"
        else
            echo "  ⊘ $agent skipped"
        fi
        return 0  # Don't fail, just skip
    fi
}

configure_agent "claude" "Claude API key"
echo ""
configure_agent "grok" "Grok API key"
echo ""
configure_agent "gemini" "Gemini API key"
echo ""
configure_agent "groq" "Groq API key (FREE)"
echo ""
configure_agent "huggingface" "HuggingFace API token (FREE)"

echo ""
echo "=========================================="
echo "Done! Test with: make test"
echo "=========================================="
