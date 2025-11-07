# Phase 2: AI Model Containers Deployment

**Deploy Claude, Grok, and Gemini CLI tools in isolated containers**

---

## Quick Start

### Prerequisites
- Phase 1 complete (run `sudo podman pod ps` to verify `ai-agents` pod exists)
- Internet connection for pulling Python packages

### Step 1: Run Setup Script

```bash
cd /home/aiagent/ai-setup
sudo bash setup-phase2.sh
```

**The script will:**
1. Create Dockerfiles for Claude, Grok, Gemini
2. Build container images with AI SDKs
3. Stop test container
4. Launch all 3 AI containers
5. Verify each container works

**Time:** ~3-5 minutes (depending on download speed)

### Step 2: Verify Containers

```bash
sudo podman ps --pod
# Should show: claude-agent, grok-agent, gemini-agent

# Test each container
sudo podman exec claude-agent python3 -c "import anthropic; print('Claude SDK ready')"
sudo podman exec grok-agent python3 -c "import requests; print('Grok ready')"
sudo podman exec gemini-agent python3 -c "import google.generativeai; print('Gemini SDK ready')"
```

**Phase 2 Complete** ✅ → Ready for Phase 3 (authentication & configuration)

---

## What's Deployed

### Container Architecture

```
ai-agents pod (rootful)
├── claude-agent    (Anthropic SDK)
├── grok-agent      (xAI API tools)
└── gemini-agent    (Google SDK)
```

### Container Details

| Container | Image | SDK Installed | Workspace | Status |
|-----------|-------|---------------|-----------|--------|
| claude-agent | ai-claude:latest | anthropic | /ai/claude | Running |
| grok-agent | ai-grok:latest | requests | /ai/grok | Running |
| gemini-agent | ai-gemini:latest | google-generativeai | /ai/gemini | Running |

### Volume Mounts

Each container mounts:
- **Own workspace** (RW): `/ai/{model}/`
- **Shared knowledge** (RO): `/ai/shared/`
- **Audit logs** (W): `/ai/logs/`

---

## Daily Usage

```bash
# Access Claude container
sudo podman exec -it claude-agent /bin/bash

# Access Grok container
sudo podman exec -it grok-agent /bin/bash

# Access Gemini container
sudo podman exec -it gemini-agent /bin/bash

# Run Python script in container
sudo podman exec claude-agent python3 /ai/claude/workspace/script.py

# Check all containers status
sudo podman ps --pod
```

---

## Container Images

### Base Image (ai-base:secure)
- Ubuntu 22.04
- Python 3.10 + pip
- curl, jq
- Non-root user (agent:1001)

### Claude Image (ai-claude:latest)
```
FROM ai-base:secure
+ anthropic SDK
+ python-dotenv
```

### Grok Image (ai-grok:latest)
```
FROM ai-base:secure
+ requests
+ python-dotenv
```

### Gemini Image (ai-gemini:latest)
```
FROM ai-base:secure
+ google-generativeai
+ python-dotenv
```

---

## Next: Phase 3

**Configuration & Authentication:**
1. Set up API credentials/auth for each service
2. Create wrapper scripts for CLI access
3. Configure agent behavior and parameters
4. Test inter-agent communication
5. Implement session persistence

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Container build fails | Check internet connection, retry script |
| SDK import fails | Rebuild image: `sudo bash setup-phase2.sh` |
| Container not running | `sudo podman pod restart ai-agents` |
| Permission denied | Verify Phase 1 completed correctly |

---

## Files Created

```
/home/aiagent/ai-setup/
├── Dockerfile.claude     # Claude container definition
├── Dockerfile.grok       # Grok container definition
├── Dockerfile.gemini     # Gemini container definition
└── setup-phase2.sh       # Automated setup script
```

---

## Manual Steps (If Needed)

If you prefer manual control or the script fails:

### 1. Create Dockerfiles
```bash
cd /home/aiagent/ai-setup

# See setup-phase2.sh for Dockerfile contents
```

### 2. Build Images
```bash
sudo podman build -t ai-claude:latest -f Dockerfile.claude .
sudo podman build -t ai-grok:latest -f Dockerfile.grok .
sudo podman build -t ai-gemini:latest -f Dockerfile.gemini .
```

### 3. Launch Containers
```bash
USER_UID=$(id -u)
USER_GID=$(id -g)

sudo podman run -d --pod ai-agents --name claude-agent \
  --user $USER_UID:$USER_GID \
  -v /ai/claude:/ai/claude:rw \
  -v /ai/shared:/ai/shared:ro \
  -v /ai/logs:/ai/logs:rw \
  ai-claude:latest sleep infinity

sudo podman run -d --pod ai-agents --name grok-agent \
  --user $USER_UID:$USER_GID \
  -v /ai/grok:/ai/grok:rw \
  -v /ai/shared:/ai/shared:ro \
  -v /ai/logs:/ai/logs:rw \
  ai-grok:latest sleep infinity

sudo podman run -d --pod ai-agents --name gemini-agent \
  --user $USER_UID:$USER_GID \
  -v /ai/gemini:/ai/gemini:rw \
  -v /ai/shared:/ai/shared:ro \
  -v /ai/logs:/ai/logs:rw \
  ai-gemini:latest sleep infinity
```

---

## Performance Notes

- **Image sizes:** ~200-300MB each (minimal Python + SDK)
- **Build time:** 2-4 minutes total for all 3 images
- **Runtime overhead:** ~100ms per command (same as Phase 1)
- **Memory:** ~100MB per idle container

---

## Document Info

- **Version:** 1.0
- **Date:** November 4, 2025
- **Status:** Phase 2 - Container Deployment
- **Dependencies:** Phase 1 Complete

---
