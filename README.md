# AI Multi-Agent System
## Secure, Containerized AI Access via Terminal

**Deploy Claude, Grok, and Gemini in isolated containers with encrypted credentials and CLI access.**

[![Status](https://img.shields.io/badge/Status-Phase%204%20Complete-green)]()
[![Tested](https://img.shields.io/badge/Tested-Ubuntu%2022.04-blue)]()
[![Deploy Time](https://img.shields.io/badge/Deploy-5--10%20min-brightgreen)]()

---

## Quick Start

```bash
# Clone repository
git clone <your-repo-url>
cd ai-agents-multi-model

# Deploy everything (Phase 1-4)
make deploy-full

# Or step by step:
make install          # Prerequisites
make deploy           # Phase 1-3 (foundation)
make deploy-phase4    # Phase 4 (full APIs + conversation history)
```

**That's it!** In 5-10 minutes you'll have:
- ✅ 3 AI agents in isolated containers
- ✅ Full API implementations with conversation memory
- ✅ Encrypted credential storage
- ✅ Multi-turn conversations with context management
- ✅ Host-side CLI access (`claude`, `grok`, `gemini` commands)
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

### CLI Usage (Phase 4)
```bash
# Simple commands from host (after Phase 4)
claude "Explain quantum computing"
grok "What's trending in AI?"
gemini "Calculate fibonacci sequence"

# Project-specific conversations
claude --context myproject "Let's design the authentication system"
claude --context myproject "What about OAuth2 flow?"

# Context management
claude --list                    # List all conversation contexts
claude --switch another-project  # Switch active context

# Container access (Phase 1-3)
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
- [Claude.ai](https://claude.ai) - Pro/Team subscription
- [X.ai](https://x.ai) - Grok access  
- [Google AI Studio](https://aistudio.google.com) - Free API key

---

## Installation

### Using Makefile (Recommended)

```bash
make install        # Install prerequisites
make deploy-full    # Deploy everything (Phase 1-4)
make status         # Check status
make contexts       # Show conversation contexts
make test           # Test agents
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

### Phase 4 Commands (Recommended)

```bash
# Simple queries from anywhere on host
claude "Explain quantum computing"
grok "What's trending in AI security?"
gemini "Calculate fibonacci sequence in Python"

# Project-specific conversations (maintains context)
claude --context oauth-impl "I need to implement OAuth2"
claude --context oauth-impl "What grant types should I support?"
claude --context oauth-impl "Show me the authorization code flow"

# Context management
claude --list                        # List all contexts
claude --switch my-other-project     # Switch active context
grok --list                          # Works for all agents
gemini --context research "..."      # Or specify inline

# Management
make status      # System status
make contexts    # Show all conversation contexts
make restart     # Restart containers
make logs        # View logs
```

### Phase 1-3 Commands (Container Access)

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

### What Works (Phase 4) ✅
- ✅ **Claude:** Full Anthropic SDK integration with conversation history
- ✅ **Grok:** Full xAI API integration with conversation history
- ✅ **Gemini:** Full Google AI SDK with conversation history
- ✅ **Conversation Memory:** Multi-turn conversations per project/topic
- ✅ **Context Management:** Project-specific conversation isolation
- ✅ **Security:** All credentials encrypted with age
- ✅ **Container Isolation:** Proper rootful Podman isolation
- ✅ **Host CLI:** Simple `claude`, `grok`, `gemini` commands
- ✅ **Agent Bridge:** Basic agent-to-agent communication

### Phase 5 (Planned)
- 📋 Advanced agent orchestration
- 📋 Workflow engine (multi-agent workflows)
- 📋 Meta-agent conductor
- 📋 Local LLM support (Ollama, DeepSeek)

---

## Roadmap

### ✅ Phase 1-3: Foundation (Complete)
- Container infrastructure
- Encryption & security
- Basic CLI wrappers
- Base Gemini API

### ✅ Phase 4: Full APIs & Conversations (Complete)
- Full Claude API integration
- Full Grok API integration
- Enhanced Gemini API
- Conversation history per project/topic
- Multi-turn conversations with context
- Host-side CLI commands
- Basic agent-to-agent communication

### 📋 Phase 5: Advanced Orchestration (Planned)
- Workflow engine for multi-agent tasks
- Config-driven agent spawning
- Meta-agent conductor
- Local LLM support (Ollama, DeepSeek)
- Advanced agent collaboration

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

**Version:** 2.0 (Phase 4 Complete)
**Last Updated:** November 13, 2025
**Tested:** Ubuntu 22.04, Podman 4.9+

**Deploy now:** `make deploy-full` 🚀
