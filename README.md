# AI Multi-Agent System
## Secure, Containerized AI Access via Terminal

**Deploy Claude, Grok, and Gemini in isolated containers with encrypted credentials and CLI access.**

[![Status](https://img.shields.io/badge/Status-Phase%203%20Complete-green)]()
[![Tested](https://img.shields.io/badge/Tested-Ubuntu%2022.04-blue)]()
[![Deploy Time](https://img.shields.io/badge/Deploy-5--10%20min-brightgreen)]()

---

## Quick Start

```bash
# Clone repository
git clone <your-repo-url>
cd ai-agents-multi-model

# Deploy everything
make deploy

# Or manually:
sudo bash deploy.sh
```

**That's it!** In 5-10 minutes you'll have:
- ✅ 3 AI agents in isolated containers
- ✅ Encrypted credential storage  
- ✅ CLI wrappers ready to use
- ✅ Secure file system structure

---

## What You Get

### Three AI Agents
```
┌─────────────────┬──────────────────┬────────────────────┐
│  claude-agent   │   grok-agent     │   gemini-agent     │
├─────────────────┼──────────────────┼────────────────────┤
│ Anthropic       │ xAI Grok         │ Google Gemini      │
│ Claude Sonnet   │ Fast responses   │ 2.5 Flash (free)   │
│ Best reasoning  │ Conversational   │ Fully working API  │
└─────────────────┴──────────────────┴────────────────────┘
```

### Security Features
- **Podman containers** - Rootful mode with user UID isolation
- **Age encryption** - 256-bit credential storage
- **Network isolation** - Internet-only (no local network)
- **File isolation** - Only `/ai` directory accessible
- **Audit logs** - Write-only log directory

### CLI Usage
```bash
# Quick query
sudo podman exec gemini-agent /home/agent/gemini-chat "What is Kubernetes?"

# Interactive shell
sudo podman exec -it gemini-agent bash
./gemini-chat "Explain Docker"

# Using Makefile
make query    # Interactive query helper
make status   # Check system status
```

---

## Prerequisites

### System Requirements
- **OS:** Ubuntu 22.04+ (or compatible Linux)
- **RAM:** 16GB recommended
- **Disk:** 5GB free space
- **Access:** Sudo privileges

### Required Software
- Podman 4.9+
- age encryption tool

**Auto-install:**
```bash
make install
```

### AI Service Accounts
- [Claude.ai](https://claude.ai) - Pro/Team subscription
- [X.ai](https://x.ai) - Grok access  
- [Google AI Studio](https://aistudio.google.com) - Free API key

---

## Installation

### Using Makefile (Recommended)

```bash
make install    # Install prerequisites
make deploy     # Deploy everything
make status     # Check status
make test       # Test agents
```

### Manual Deployment

```bash
sudo bash deploy.sh
# Runs: Phase 1 (Foundation) → Phase 2 (Containers) → Phase 3 (Auth)
```

---

## Configuration

### 1. Extract Credentials

After deployment, configure AI credentials:

- **Claude:** https://claude.ai → F12 → Cookies → `sessionKey`
- **Grok:** https://x.ai → F12 → Cookies → `sso`
- **Gemini:** https://aistudio.google.com/app/apikey

**Full guide:** [docs/token-extraction-guide.md](docs/token-extraction-guide.md)

### 2. Encrypt Credentials

```bash
# Using Makefile
make encrypt

# Or manually
echo "YOUR_TOKEN" | age -r $(grep "public key:" ~/.age-key.txt | awk '{print $NF}') \
  -o /ai/agent/context/.secrets.age
sudo chmod 600 /ai/*/context/.secrets.age
```

### 3. Verify

```bash
make test
# Or: sudo podman exec gemini-agent /home/agent/gemini-chat "Hello"
```

---

## Usage

### Basic Commands

```bash
# Query agents
sudo podman exec gemini-agent /home/agent/gemini-chat "Your question"

# Interactive shell
sudo podman exec -it gemini-agent bash

# Management
make status      # System status
make restart     # Restart containers
make logs        # View logs
```

### Working with Files

```bash
# Share files with agents
sudo cp myfile.txt /ai/shared/

# Ask agent to analyze
sudo podman exec gemini-agent /home/agent/gemini-chat \
  "Analyze /ai/shared/myfile.txt"

# Get agent output
sudo cat /ai/gemini/workspace/output.txt
```

---

## Directory Structure

```
/ai/
├── shared/          # All agents can read
├── claude/
│   ├── context/     # Encrypted credentials
│   ├── history/     # Conversations (Phase 4)
│   └── workspace/   # Working files
├── grok/
├── gemini/
└── logs/           # Audit trail
```

---

## Current Status

### What Works (Phase 3)
- ✅ **Gemini:** Full API with actual responses
- ⚠️ **Claude:** Token verification (Phase 4 for full API)
- ⚠️ **Grok:** Token verification (Phase 4 for full API)
- ✅ **Security:** All credentials encrypted
- ✅ **Isolation:** Proper container isolation

### Known Limitations
- ❌ No conversation memory
- ❌ No agent-to-agent communication
- ❌ Claude/Grok APIs incomplete

**Phase 4 will address these!**

---

## Roadmap

### ✅ Phase 1-3: Foundation (Complete)
- Container infrastructure
- Encryption & security
- CLI wrappers
- Gemini API

### 🚧 Phase 4: Enhanced APIs (Next)
- Full Claude API
- Full Grok API  
- Conversation history
- Multi-turn conversations

### 📋 Phase 5: Orchestration (Planned)
- Agent-to-agent communication
- Workflow engine
- Config-driven agents
- Conductor meta-agent

---

## Troubleshooting

### Containers not running
```bash
make status
make restart
```

### Permission denied
```bash
groups | grep aiagent  # Should be in aiagent group
# If not: logout and login
```

### Cannot decrypt
```bash
ls -la ~/.age-key.txt  # Verify key exists
make encrypt           # Re-encrypt credentials
```

---

## Maintenance

```bash
make backup     # Backup /ai directory
make clean      # Remove containers
make reset      # Complete cleanup (WARNING: removes /ai)
```

---

## Documentation

- **[Token Extraction](docs/token-extraction-guide.md)** - Get API tokens
- **[Age Encryption](docs/age-encryption-guide.md)** - Security details
- **[Phase Details](docs/)** - Implementation specifics

---

## Security

**Protected:**
- ✅ Encrypted credentials (age 256-bit)
- ✅ Container isolation
- ✅ Network restrictions
- ✅ Audit logging

**Best Practices:**
- Backup `~/.age-key.txt` securely
- Rotate credentials every 30-90 days
- Review `/ai/logs/` regularly
- Never commit secrets to git

---

## FAQ

**Why Podman?** Rootless capability, no daemon, better security  
**Why rootful?** Permission issues with rootless (containers still run as your UID)  
**Add more models?** Phase 4 enables easy config-driven agents  
**Production ready?** Yes for individual use, Phase 5 adds team features

---

## License

MIT License

---

**Version:** 1.0 (Phase 3 Complete)  
**Last Updated:** November 2025  
**Tested:** Ubuntu 22.04, Podman 4.9+

**Deploy now:** `make deploy` 🚀
