#!/bin/bash
# AI Multi-Agent System - Master Deployment Script
# Runs Phase 1, 2, and 3 in sequence
# Usage: sudo bash deploy.sh

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "=========================================="
echo "AI Multi-Agent System Deployment"
echo "=========================================="
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}ERROR: This script must be run with sudo${NC}"
    echo "Usage: sudo bash deploy.sh"
    exit 1
fi

# Get actual user
ACTUAL_USER=${SUDO_USER:-$USER}
echo "Deploying for user: $ACTUAL_USER"
echo ""

# Check prerequisites
echo "Checking prerequisites..."

# Check Podman
if ! command -v podman &> /dev/null; then
    echo -e "${YELLOW}Podman not found. Installing...${NC}"
    apt update >/dev/null 2>&1
    apt install -y podman >/dev/null 2>&1
    echo -e "${GREEN}✓ Podman installed${NC}"
else
    echo -e "${GREEN}✓ Podman already installed${NC}"
fi

# Check age
if ! command -v age &> /dev/null; then
    echo -e "${YELLOW}Age not found. Installing...${NC}"
    apt update >/dev/null 2>&1
    apt install -y age >/dev/null 2>&1
    echo -e "${GREEN}✓ Age installed${NC}"
else
    echo -e "${GREEN}✓ Age already installed${NC}"
fi

echo ""
echo "=========================================="
echo "Phase 1: Foundation & Security Setup"
echo "=========================================="
echo ""

if [ -f "scripts/setup-ai-foundation.sh" ]; then
    bash scripts/setup-phase1.sh
else
    echo -e "${RED}ERROR: scripts/setup-ai-foundation.sh not found${NC}"
    echo "Make sure you're running this from the repository root"
    exit 1
fi

echo ""
echo "=========================================="
echo "Phase 2: AI Container Deployment"
echo "=========================================="
echo ""

if [ -f "scripts/setup-phase2.sh" ]; then
    bash scripts/setup-phase2.sh
else
    echo -e "${RED}ERROR: scripts/setup-phase2.sh not found${NC}"
    exit 1
fi

echo ""
echo "=========================================="
echo "Phase 3: Authentication & CLI Setup"
echo "=========================================="
echo ""

if [ -f "scripts/setup-phase3.sh" ]; then
    bash scripts/setup-phase3.sh
else
    echo -e "${RED}ERROR: scripts/setup-phase3.sh not found${NC}"
    exit 1
fi

echo ""
echo "=========================================="
echo "Deployment Complete!"
echo "=========================================="
echo ""

# Check credential status
CLAUDE_EXISTS=false
GROK_EXISTS=false
GEMINI_EXISTS=false

[ -f /ai/claude/context/.secrets.age ] && CLAUDE_EXISTS=true
[ -f /ai/grok/context/.secrets.age ] && GROK_EXISTS=true
[ -f /ai/gemini/context/.secrets.age ] && GEMINI_EXISTS=true

echo "System Status:"
echo "  Containers:"
sudo podman ps --filter pod=ai-agents --format "    ✓ {{.Names}}" 2>/dev/null || echo "    ✗ No containers running"
echo ""

echo "  Credentials:"
if [ "$CLAUDE_EXISTS" = true ]; then
    echo -e "    ${GREEN}✓ Claude configured${NC}"
else
    echo -e "    ${YELLOW}⚠ Claude not configured${NC}"
fi

if [ "$GROK_EXISTS" = true ]; then
    echo -e "    ${GREEN}✓ Grok configured${NC}"
else
    echo -e "    ${YELLOW}⚠ Grok not configured${NC}"
fi

if [ "$GEMINI_EXISTS" = true ]; then
    echo -e "    ${GREEN}✓ Gemini configured${NC}"
else
    echo -e "    ${YELLOW}⚠ Gemini not configured${NC}"
fi

echo ""

# Next steps based on credential status
if [ "$CLAUDE_EXISTS" = false ] || [ "$GROK_EXISTS" = false ] || [ "$GEMINI_EXISTS" = false ]; then
    echo "Next Steps:"
    echo "1. Extract AI tokens (see docs/token-extraction-guide.md)"
    echo "2. Encrypt credentials:"
    echo ""
    
    PUBLIC_KEY=$(grep "public key:" ~$ACTUAL_USER/.age-key.txt 2>/dev/null | awk '{print $NF}' || echo "YOUR_PUBLIC_KEY")
    
    if [ "$CLAUDE_EXISTS" = false ]; then
        echo "   Claude:"
        echo "   echo 'YOUR_CLAUDE_TOKEN' | age -r $PUBLIC_KEY -o /ai/claude/context/.secrets.age"
        echo ""
    fi
    
    if [ "$GROK_EXISTS" = false ]; then
        echo "   Grok:"
        echo "   echo 'YOUR_GROK_TOKEN' | age -r $PUBLIC_KEY -o /ai/grok/context/.secrets.age"
        echo ""
    fi
    
    if [ "$GEMINI_EXISTS" = false ]; then
        echo "   Gemini:"
        echo "   echo 'YOUR_GEMINI_KEY' | age -r $PUBLIC_KEY -o /ai/gemini/context/.secrets.age"
        echo ""
    fi
    
    echo "3. Fix permissions: sudo chmod 600 /ai/*/context/.secrets.age"
    echo "4. Re-run: sudo bash scripts/setup-phase3.sh"
else
    echo "All credentials configured!"
    echo ""
    echo "Test Commands:"
    echo "  sudo podman exec gemini-agent /home/agent/gemini-chat \"Hello\""
    echo "  sudo podman exec claude-agent /home/agent/claude-chat \"Hello\""
    echo "  sudo podman exec grok-agent /home/agent/grok-chat \"Hello\""
fi

echo ""
echo "Documentation: docs/"
echo "Age Guide: docs/age-encryption-guide.md"
echo "Token Guide: docs/token-extraction-guide.md"
echo ""
