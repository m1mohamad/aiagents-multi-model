#!/bin/bash
# Phase 4.5: Project-Level Organization & Knowledge Extraction
# Adds project management and smart context loading to Phase 4
# Usage: sudo bash setup-phase4.5.sh

set -e

if [ "$EUID" -ne 0 ]; then
    echo "ERROR: This script must be run with sudo"
    echo "Usage: sudo bash setup-phase4.5.sh"
    exit 1
fi

ACTUAL_USER=${SUDO_USER:-$USER}
USER_HOME=$(eval echo ~$ACTUAL_USER)
USER_UID=$(id -u $ACTUAL_USER)
USER_GID=$(id -g $ACTUAL_USER)
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "=========================================="
echo "Phase 4.5: Project Management & Knowledge"
echo "=========================================="
echo "User: $ACTUAL_USER"
echo ""

# Step 1: Verify prerequisites
echo "[1/5] Verifying prerequisites..."

# Check Phase 4 is complete
if ! podman ps --filter "name=claude-agent" --format "{{.Names}}" | grep -q "claude-agent"; then
    echo "✗ claude-agent not running. Please complete Phase 4 first."
    exit 1
fi

if ! podman ps --filter "name=grok-agent" --format "{{.Names}}" | grep -q "grok-agent"; then
    echo "✗ grok-agent not running. Please complete Phase 4 first."
    exit 1
fi

if ! podman ps --filter "name=gemini-agent" --format "{{.Names}}" | grep -q "gemini-agent"; then
    echo "✗ gemini-agent not running. Please complete Phase 4 first."
    exit 1
fi

# Check that history directories exist
if [ ! -d /ai/claude/history ]; then
    echo "✗ /ai/claude/history not found. Please complete Phase 4 first."
    exit 1
fi

echo "✓ Phase 4 prerequisites met"
echo ""

# Step 2: Create project metadata files (non-destructive)
echo "[2/5] Initializing project metadata..."

for agent in claude grok gemini; do
    projects_file="/ai/$agent/history/projects.json"

    # Only create if doesn't exist (non-destructive)
    if [ ! -f "$projects_file" ]; then
        echo '{"projects": {}}' > "$projects_file"
        chown $ACTUAL_USER:aiagent "$projects_file"
        chmod 640 "$projects_file"
        echo "  ✓ Created projects.json for $agent"
    else
        echo "  - projects.json already exists for $agent (preserving)"
    fi
done

echo ""

# Step 3: Install updated Python package structure in containers
echo "[3/5] Installing Python package structure..."

for agent in claude grok gemini; do
    echo "  Updating ${agent}-agent..."

    # Create package directory structure in container
    podman exec -u root ${agent}-agent mkdir -p /home/agent/ai_agents/core

    # Copy package files
    podman cp "$PROJECT_ROOT/src/ai_agents/__init__.py" ${agent}-agent:/home/agent/ai_agents/
    podman cp "$PROJECT_ROOT/src/ai_agents/__about__.py" ${agent}-agent:/home/agent/ai_agents/
    podman cp "$PROJECT_ROOT/src/ai_agents/core/__init__.py" ${agent}-agent:/home/agent/ai_agents/core/
    podman cp "$PROJECT_ROOT/src/ai_agents/core/project_manager.py" ${agent}-agent:/home/agent/ai_agents/core/

    # Copy knowledge extractor (Claude only needs it, but install in all for consistency)
    podman cp "$PROJECT_ROOT/src/ai_agents/core/knowledge_extractor.py" ${agent}-agent:/home/agent/ai_agents/core/

    # Copy updated API implementation
    podman cp "$PROJECT_ROOT/src/ai_agents/${agent}_api.py" ${agent}-agent:/home/agent/ai_agents/

    # Set permissions
    podman exec -u root ${agent}-agent chown -R $USER_UID:$USER_GID /home/agent/ai_agents
    podman exec -u root ${agent}-agent chmod -R 755 /home/agent/ai_agents

    # Create symlink for backward compatibility (so old /home/agent/claude-api.py still works)
    podman exec -u root ${agent}-agent ln -sf /home/agent/ai_agents/${agent}_api.py /home/agent/${agent}-api.py 2>/dev/null || true

    echo "    ✓ Package structure installed"
done

echo ""

# Step 4: Update CLI wrappers to use new package
echo "[4/5] Updating CLI wrappers..."

for agent in claude grok gemini; do
    cat > /tmp/${agent}-chat << EOF
#!/bin/bash
cd /home/agent
export PYTHONPATH=/home/agent:\$PYTHONPATH
exec python3 -m ai_agents.${agent}_api "\$@"
EOF

    podman cp /tmp/${agent}-chat ${agent}-agent:/home/agent/${agent}-chat
    podman exec -u root ${agent}-agent chmod +x /home/agent/${agent}-chat
    podman exec -u root ${agent}-agent chown $USER_UID:$USER_GID /home/agent/${agent}-chat
    rm -f /tmp/${agent}-chat

    echo "  ✓ Updated ${agent}-chat wrapper"
done

echo ""

# Step 5: Test installations
echo "[5/5] Testing installations..."

# Test imports in each container
for agent in claude grok gemini; do
    echo -n "  Testing ${agent}-agent: "

    if podman exec ${agent}-agent python3 -c "from ai_agents.core.project_manager import ProjectManager; print('✓')" 2>/dev/null; then
        echo "✓ Package imports OK"
    else
        echo "✗ Import failed"
        echo "    Trying to diagnose..."
        podman exec ${agent}-agent python3 -c "import sys; print('PYTHONPATH:', sys.path)"
    fi
done

# Test Claude-specific knowledge extractor
echo -n "  Testing knowledge extractor (Claude): "
if podman exec claude-agent python3 -c "from ai_agents.core.knowledge_extractor import KnowledgeExtractor; print('✓')" 2>/dev/null; then
    echo "✓ OK"
else
    echo "✗ Failed"
fi

echo ""

# Success summary
echo "=========================================="
echo "Phase 4.5 Complete!"
echo "=========================================="
echo ""

echo "New Features Available:"
echo ""
echo "  Project Management:"
echo "    claude --project myproject \"message\"   # Create/use project context"
echo "    claude --projects                      # List all projects"
echo "    grok --project myproject \"message\""
echo "    gemini --project myproject \"message\""
echo ""
echo "  Knowledge Extraction (Claude only):"
echo "    - Automatically extracts decisions, facts, and patterns"
echo "    - Builds project knowledge base over time"
echo "    - Smart context loading reduces token usage"
echo ""
echo "  All previous Phase 4 commands still work:"
echo "    claude \"message\"                       # Use default context"
echo "    claude --context NAME \"message\"        # Use specific context"
echo "    claude --list                          # List contexts"
echo "    claude --switch CONTEXT                # Switch context"
echo ""

echo "Project Metadata Locations:"
echo "  /ai/claude/history/projects.json"
echo "  /ai/grok/history/projects.json"
echo "  /ai/gemini/history/projects.json"
echo ""

echo "Quick Test:"
echo "  claude --project test-project \"Hello! This is a test.\""
echo "  claude --projects"
echo ""
echo "Documentation: docs/phase4.5-projects.md"
echo ""
