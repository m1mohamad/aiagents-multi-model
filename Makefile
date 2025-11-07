# Makefile for AI Multi-Agent System
# Simplifies deployment and management

.PHONY: help install deploy test clean restart status logs

# Default target
help:
	@echo "AI Multi-Agent System - Available Commands:"
	@echo ""
	@echo "  make install    - Install prerequisites (podman, age)"
	@echo "  make deploy     - Run full deployment (Phase 1-3)"
	@echo "  make test       - Verify all components working"
	@echo "  make status     - Show system status"
	@echo "  make logs       - Show container logs"
	@echo "  make restart    - Restart all containers"
	@echo "  make stop       - Stop all containers"
	@echo "  make start      - Start all containers"
	@echo "  make clean      - Remove all containers and pod"
	@echo "  make reset      - Complete cleanup (containers + /ai directory)"
	@echo ""
	@echo "Quick Start: make install && make deploy"

# Install prerequisites
install:
	@echo "Installing prerequisites..."
	@command -v podman >/dev/null || (sudo apt update && sudo apt install -y podman)
	@command -v age >/dev/null || sudo apt install -y age
	@echo "✓ Prerequisites installed"

# Full deployment (Phase 1-3)
deploy:
	@echo "Starting full deployment..."
	@sudo bash deploy.sh

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
	@echo "=== Directory Structure ==="
	@ls -lh /ai/ 2>/dev/null || echo "/ai directory not created yet"

# Show container logs
logs:
	@echo "Select container: [claude|grok|gemini]"
	@read -p "Container: " container; \
	sudo podman logs $${container}-agent

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
