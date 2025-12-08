# AI Multi-Agent System
## Secure, Containerized AI Access via Terminal

**Deploy Claude, Grok, and Gemini in isolated containers with encrypted credentials and CLI access.**

[![Status](https://img.shields.io/badge/Status-Production%20Ready-green)]()
[![Tested](https://img.shields.io/badge/Tested-Ubuntu%2022.04-blue)]()
[![Deploy Time](https://img.shields.io/badge/Deploy-5--10%20min-brightgreen)]()
[![Configuration](https://img.shields.io/badge/Full%20APIs-Configured-blue)]()


---

## Quick Start

```bash
# Clone repository
git clone <your-repo-url>
cd ai-agents-multi-model

# Deploy everything
make deploy-full

# Or step by step:
make install    # Prerequisites
make deploy     # Infrastructure (containers, security)
make secrets    # Interactive key setup
make config     # Full APIs & conversation history
```

**That's it!** In 5-10 minutes you'll have:
- ✅ 3 AI agents in isolated containers
- ✅ Full API implementations with conversation memory
- ✅ Encrypted credential storage
- ✅ Multi-turn conversations with context management
- ✅ Host-side CLI access (`ai-claude`, `ai-grok`, `ai-gemini` commands)
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

### CLI Usage (After Configuration)
```bash
# Simple commands from host (after running 'make config')
ai-claude "Explain quantum computing"
ai-grok "What's trending in AI?"
ai-gemini "Calculate fibonacci sequence"

# Project-specific conversations
ai-claude --context myproject "Let's design the authentication system"
ai-claude --context myproject "What about OAuth2 flow?"

# Context management
ai-claude --list                    # List all conversation contexts
ai-claude --switch another-project  # Switch active context

# Container access (basic deployment)
sudo podman exec gemini-agent /home/agent/gemini-chat "What is Kubernetes?"
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
- [Anthropic Console](https://console.anthropic.com/settings/keys) - Claude API key (paid)
- [X.ai](https://x.ai) - Grok access (Premium subscription)
- [Google AI Studio](https://aistudio.google.com) - Gemini API key (free tier)

---

## Installation

### Using Makefile (Recommended)

```bash
make install      # Install prerequisites
make deploy       # Deploy infrastructure
make secrets      # Configure API keys interactively
make config       # Configure full APIs & conversation history
make status       # Check status
make contexts     # Show conversation contexts
make test         # Test agents
```

### Manual Deployment

```bash
# Deploy infrastructure
sudo bash deploy.sh

# Configure full APIs
sudo bash scripts/setup-phase4.sh
```

---

## Configuration

### Configure API Keys

After deployment, configure your API keys:

```bash
make secrets
```

The script will prompt for each API key. Get keys from:
- **Claude**: https://console.anthropic.com/settings/keys (API Keys)
- **Grok**: https://console.x.ai (API Keys)
- **Gemini**: https://aistudio.google.com/app/apikey (API Key)

All keys are encrypted with age before storage.

**Detailed guides:**
- Claude: [docs/claude-api-key-setup.md](docs/claude-api-key-setup.md)
- Grok/Gemini: [docs/token-extraction-guide.md](docs/token-extraction-guide.md)

### Verify

```bash
make test
# Or: sudo podman exec gemini-agent /home/agent/gemini-chat "Hello"
```

---

## Usage

### Recommended Usage (After Configuration)

```bash
# Simple queries from anywhere on host
ai-claude "Explain quantum computing"
ai-grok "What's trending in AI security?"
ai-gemini "Calculate fibonacci sequence in Python"

# Project-specific conversations (maintains context)
ai-claude --context oauth-impl "I need to implement OAuth2"
ai-claude --context oauth-impl "What grant types should I support?"
ai-claude --context oauth-impl "Show me the authorization code flow"

# Context management
ai-claude --list                        # List all contexts
ai-claude --switch my-other-project     # Switch active context
ai-grok --list                          # Works for all agents
ai-gemini --context research "..."      # Or specify inline

# Management
make status      # System status
make contexts    # Show all conversation contexts
make restart     # Restart containers
make logs        # View logs
```

### Alternative: Direct Container Access

```bash
# Query agents directly
sudo podman exec gemini-agent /home/agent/gemini-chat "Your question"

# Interactive shell
sudo podman exec -it gemini-agent bash
./gemini-chat "Hello"
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

### What Works ✅
- ✅ **Infrastructure:** Secure containerized deployment with Podman
- ✅ **Full API Implementations:** Claude, Grok, and Gemini with complete SDK integration
- ✅ **Conversation Memory:** Multi-turn conversations per project/topic
- ✅ **Context Management:** Project-specific conversation isolation
- ✅ **Security:** All credentials encrypted with age encryption
- ✅ **Container Isolation:** Proper rootful Podman with network restrictions
- ✅ **Host CLI:** Simple `ai-claude`, `ai-grok`, `ai-gemini` commands available system-wide
- ✅ **Agent Communication:** Basic agent-to-agent messaging

### Future Enhancements (Planned)
- 📋 Advanced agent orchestration workflows
- 📋 Workflow engine for multi-agent task automation
- 📋 Meta-agent conductor for intelligent routing
- 📋 Local LLM support (Ollama, DeepSeek integration)

---

## Implementation Roadmap

### ✅ Infrastructure Deployment (Complete)
- Podman container orchestration
- Age encryption for credentials
- Network and file system isolation
- Base container images
- Security boundaries

### ✅ Full API Configuration (Complete)
- Claude Anthropic SDK integration
- Grok xAI API integration
- Gemini Google AI SDK integration
- Conversation history persistence
- Multi-turn context management
- Host-side CLI commands (`ai-claude`, `ai-grok`, `ai-gemini`)
- Agent-to-agent communication bridge

### 📋 Advanced Features (Future)
- Workflow automation engine
- Config-driven agent orchestration
- Meta-agent intelligent routing
- Local LLM integration (Ollama, DeepSeek)
- Advanced multi-agent collaboration

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

**Version:** 2.0 (Production Ready)
**Last Updated:** November 13, 2025
**Tested:** Ubuntu 22.04, Podman 4.9+

**Deploy now:** `make deploy-full` 🚀
