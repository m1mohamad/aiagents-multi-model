# Makefile for AI Multi-Agent System
# Simplifies deployment and management

.PHONY: help install deploy secrets config reconfigure deploy-full update test clean restart status logs

# Default target
help:
	@echo "AI Multi-Agent System - Available Commands:"
	@echo ""
	@echo "Deployment:"
	@echo "  make install       - Install prerequisites (podman, age)"
	@echo "  make deploy        - Deploy infrastructure (containers, security)"
	@echo "  make secrets       - Configure API keys interactively"
	@echo "  make config        - Configure full APIs & conversation history"
	@echo "  make update        - SAFE: Update code, preserve secrets/data"
	@echo "  make reconfigure   - Re-apply configuration (if needed)"
	@echo "  make deploy-full   - ⚠️  DESTRUCTIVE: Fresh install (destroys data)"
	@echo ""
	@echo "Management (Bash):"
	@echo "  make test          - Verify all components working"
	@echo "  make status        - Show system status"
	@echo "  make diagnose      - Run system diagnostics"
	@echo "  make contexts      - Show conversation contexts"
	@echo "  make restart       - Restart all containers"
	@echo "  make stop          - Stop all containers"
	@echo "  make start         - Start all containers"
	@echo "  make logs          - Show container logs"
	@echo ""
	@echo "Management (Python):"
	@echo "  make py-status     - Deployment status (Python modules)"
	@echo "  make py-containers - Container status (Python modules)"
	@echo "  make py-backup     - Create backup (Python modules)"
	@echo "  make py-restart    - Restart containers (Python)"
	@echo "  make py-help       - Show all Python commands"
	@echo ""
	@echo "Cleanup:"
	@echo "  make clean         - Remove containers and pod"
	@echo "  make reset         - Complete cleanup (WARNING: removes /ai)"
	@echo ""
	@echo "Quick Start: make install && make deploy-full"

# Install prerequisites
install:
	@echo "Installing prerequisites..."
	@command -v podman >/dev/null || (sudo apt update && sudo apt install -y podman)
	@command -v age >/dev/null || sudo apt install -y age
	@echo "✓ Prerequisites installed"

# Deploy infrastructure (containers, security, base setup)
deploy:
	@echo "Deploying infrastructure..."
	@sudo bash deploy.sh

# Configure API keys interactively
secrets:
	@echo "Configuring API keys..."
	@sudo bash scripts/configure-secrets.sh

# Configure full APIs and conversation history
config:
	@echo "Configuring full APIs & conversation history..."
	@sudo bash scripts/setup-phase4.sh

# Reconfigure (re-apply configuration)
reconfigure: config
	@echo "✓ Configuration reapplied"

# Safe update - preserves secrets and data
update:
	@echo "Running safe update (preserves secrets/data)..."
	@sudo bash scripts/safe-update.sh

# Complete deployment and configuration
deploy-full: deploy config
	@echo ""
	@echo "=========================================="
	@echo "✓ Complete setup finished!"
	@echo "=========================================="
	@echo ""
	@echo "Infrastructure deployed and agents configured."
	@echo "Use 'claude', 'grok', or 'gemini' commands from anywhere."
	@echo ""

# Test all components
test:
	@echo "Testing AI agents..."
	@echo ""
	@echo "Testing Gemini (should respond):"
	@sudo podman exec gemini-agent /home/agent/gemini-chat "Hello" || echo "✗ Gemini failed"
	@echo ""
	@echo "Testing Claude (token verification):"
	@sudo podman exec claude-agent /home/agent/claude-chat "Hello" || echo "✗ Claude failed"
	@echo ""
	@echo "Testing Grok (token verification):"
	@sudo podman exec grok-agent /home/agent/grok-chat "Hello" || echo "✗ Grok failed"

# Show system status
status:
	@echo "=== Pod Status ==="
	@sudo podman pod ps
	@echo ""
	@echo "=== Container Status ==="
	@sudo podman ps --filter pod=ai-agents
	@echo ""
	@echo "=== Credentials Status ==="
	@test -f /ai/claude/context/.secrets.age && echo "✓ Claude configured" || echo "✗ Claude not configured"
	@test -f /ai/grok/context/.secrets.age && echo "✓ Grok configured" || echo "✗ Grok not configured"
	@test -f /ai/gemini/context/.secrets.age && echo "✓ Gemini configured" || echo "✗ Gemini not configured"
	@echo ""
	@echo "=== Configuration Status ==="
	@test -f /usr/local/bin/claude && echo "✓ Full APIs configured (host CLI available)" || echo "✗ Full APIs not configured yet (run 'make config')"
	@echo ""
	@echo "=== Directory Structure ==="
	@ls -lh /ai/ 2>/dev/null || echo "/ai directory not created yet"

# Show conversation contexts
contexts:
	@echo "=== Claude Contexts ==="
	@test -d /ai/claude/history && ls -1 /ai/claude/history | grep -v "^\\." || echo "No contexts found"
	@echo ""
	@echo "=== Grok Contexts ==="
	@test -d /ai/grok/history && ls -1 /ai/grok/history | grep -v "^\\." || echo "No contexts found"
	@echo ""
	@echo "=== Gemini Contexts ==="
	@test -d /ai/gemini/history && ls -1 /ai/gemini/history | grep -v "^\\." || echo "No contexts found"

# Show container logs
logs:
	@echo "Enter container name (claude-agent, grok-agent, or gemini-agent):"
	@read -p "Container: " container; \
	echo "Fetching logs for $$container..."; \
	sudo podman logs $$container 2>&1 || echo "Error: Failed to get logs for $$container"

# Diagnostic check
diagnose:
	@echo "=== System Diagnostics ==="
	@echo ""
	@echo "1. Checking /ai directory..."
	@sudo ls -lah /ai 2>/dev/null || echo "✗ /ai directory not found"
	@echo ""
	@echo "2. Checking /ai contents..."
	@sudo du -sh /ai/* 2>/dev/null || echo "✗ No contents in /ai"
	@echo ""
	@echo "3. Checking containers..."
	@sudo podman ps --filter pod=ai-agents --format "{{.Names}}: {{.Status}}"
	@echo ""
	@echo "4. Checking age key..."
	@test -f ~/.age-key.txt && echo "✓ Age key exists" || echo "✗ Age key missing"
	@test -f ~/.age-key.txt && stat -c "Permissions: %a" ~/.age-key.txt
	@echo ""
	@echo "5. Checking secrets..."
	@for agent in claude grok gemini; do \
		if [ -f "/ai/$$agent/context/.secrets.age" ]; then \
			echo "✓ $$agent secrets exist"; \
		else \
			echo "✗ $$agent secrets missing"; \
		fi; \
	done
	@echo ""
	@echo "6. Checking backup directory..."
	@ls -lh ~/ai-backups/*.age 2>/dev/null || echo "No backups found in ~/ai-backups"

# Restart all containers
restart:
	@echo "Restarting all containers..."
	@sudo podman pod restart ai-agents
	@echo "✓ Containers restarted"

# Stop all containers
stop:
	@echo "Stopping all containers..."
	@sudo podman pod stop ai-agents
	@echo "✓ Containers stopped"

# Start all containers
start:
	@echo "Starting all containers..."
	@sudo podman pod start ai-agents
	@echo "✓ Containers started"

# Remove containers and pod
clean:
	@echo "Removing containers and pod..."
	@sudo podman pod exists ai-agents && sudo podman pod rm -f ai-agents || echo "Pod already removed"
	@sudo podman rmi -f ai-claude:latest ai-grok:latest ai-gemini:latest ai-base:secure 2>/dev/null || true
	@echo "✓ Cleanup complete"

# Complete reset (WARNING: removes /ai directory)
reset: clean
	@echo "WARNING: This will remove /ai directory and all data!"
	@read -p "Are you sure? [y/N] " confirm; \
	if [ "$$confirm" = "y" ]; then \
		sudo rm -rf /ai; \
		echo "✓ Complete reset done"; \
	else \
		echo "Reset cancelled"; \
	fi

# Development helpers
dev-shell:
	@echo "Select agent: [claude|grok|gemini]"
	@read -p "Agent: " agent; \
	sudo podman exec -it $${agent}-agent bash

# Quick query to any agent
query:
	@echo "Select agent: [claude|grok|gemini]"
	@read -p "Agent: " agent; \
	read -p "Query: " query; \
	sudo podman exec $${agent}-agent /home/agent/$${agent}-chat "$$query"

# Encrypt credentials helper
encrypt:
	@echo "Credential Encryption Helper"
	@echo ""
	@echo "Your age public key:"
	@grep "public key:" ~/.age-key.txt 2>/dev/null || echo "Error: Age key not found. Run 'make deploy' first."
	@echo ""
	@echo "Select agent: [claude|grok|gemini]"
	@read -p "Agent: " agent; \
	read -p "Enter token/key: " token; \
	pubkey=$$(grep "public key:" ~/.age-key.txt | awk '{print $$NF}'); \
	echo "$$token" | age -r $$pubkey -o /ai/$$agent/context/.secrets.age; \
	sudo chmod 600 /ai/$$agent/context/.secrets.age; \
	echo "✓ Credential encrypted for $$agent"

# Backup /ai directory
backup:
	@echo "Creating backup..."
	@timestamp=$$(date +%Y%m%d-%H%M%S); \
	sudo tar -czf ~/ai-backup-$$timestamp.tar.gz /ai; \
	echo "✓ Backup created: ~/ai-backup-$$timestamp.tar.gz"

# Package for VM deployment
package:
	@echo "Creating deployment package..."
	@bash package-for-vm.sh
	@echo "✓ Package ready in /tmp/"

# ============================================
# Python Deployment Module Commands
# ============================================

# Show detailed status using Python modules
py-status:
	@echo "Running Python deployment status check..."
	@sudo python3 scripts/deploy-cli.py status

# Show container status using Python modules
py-containers:
	@echo "Checking container status via Python..."
	@sudo python3 scripts/deploy-cli.py container-status

# Verify secrets using Python modules
py-verify-secrets:
	@echo "Verifying secrets configuration..."
	@sudo python3 scripts/deploy-cli.py verify-secrets

# Restart containers using Python modules
py-restart:
	@echo "Restarting containers via Python..."
	@sudo python3 scripts/deploy-cli.py restart

# Stop containers using Python modules
py-stop:
	@echo "Stopping containers via Python..."
	@sudo python3 scripts/deploy-cli.py stop

# Start containers using Python modules
py-start:
	@echo "Starting containers via Python..."
	@sudo python3 scripts/deploy-cli.py start

# Create backup using Python modules
py-backup:
	@echo "Creating backup via Python..."
	@sudo python3 scripts/deploy-cli.py backup

# Create backup without secrets
py-backup-nosecrets:
	@echo "Creating backup (excluding secrets)..."
	@sudo python3 scripts/deploy-cli.py backup --no-secrets

# List backups using Python modules
py-list-backups:
	@echo "Listing backups..."
	@sudo python3 scripts/deploy-cli.py list-backups

# Run Python deployment tests
py-test:
	@echo "Running Python deployment module tests..."
	@python -m pytest tests/deployment/ -v

# Show Python CLI help
py-help:
	@echo "Python Deployment Module Commands:"
	@echo ""
	@echo "Status & Verification:"
	@echo "  make py-status           - Show deployment status (Python)"
	@echo "  make py-containers       - Show container status (Python)"
	@echo "  make py-verify-secrets   - Verify secrets configuration"
	@echo "  make py-test             - Run deployment module tests"
	@echo ""
	@echo "Container Management:"
	@echo "  make py-restart          - Restart all containers (Python)"
	@echo "  make py-stop             - Stop all containers (Python)"
	@echo "  make py-start            - Start all containers (Python)"
	@echo ""
	@echo "Backup Management:"
	@echo "  make py-backup           - Create backup (Python)"
	@echo "  make py-backup-nosecrets - Create backup without secrets"
	@echo "  make py-list-backups     - List available backups"
	@echo ""
	@echo "Direct CLI:"
	@echo "  sudo python3 scripts/deploy-cli.py <command>"
