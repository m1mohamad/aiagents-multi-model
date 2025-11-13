# Phase 4: Full API & Conversation History

**Production-ready AI agents with conversation persistence and context management**

---

## What's New in Phase 4

### ✅ Full API Implementations
- **Claude**: Complete Anthropic SDK integration (not just token validation)
- **Grok**: xAI API with full chat capabilities
- **Gemini**: Enhanced Google AI integration with conversation support

### ✅ Conversation Persistence
- Each agent maintains conversation history per project/topic
- Multi-turn conversations with context awareness
- Automatic context management and switching

### ✅ Project/Topic Isolation
- Separate conversation threads per project
- Avoid token limit issues by dedicating contexts to specific topics
- Easy context switching and management

---

## Installation

### Prerequisites
- Phase 1-3 complete (containers running)
- Credentials configured for desired agents
- Python dependencies installed

### Deploy Phase 4

```bash
# From repository root
sudo bash scripts/setup-phase4.sh
```

**Time**: 2-3 minutes

---

## Usage

### Basic Commands

```bash
# From host (anywhere on system)
claude "Explain quantum computing"
grok "What's trending in AI?"
gemini "Calculate the meaning of life"
```

### Context Management

```bash
# Use specific context (project/topic)
claude --context project-auth "Review OAuth implementation"
grok --context research-ai "Latest trends in LLMs"

# Continue conversation in same context
claude --context project-auth "What about token refresh?"

# List all contexts for an agent
claude --list

# Switch active context
claude --switch project-api

# Default context (if not specified)
claude "Hello"  # Uses 'default' context
```

### Multi-turn Conversations

```bash
# Start a project-specific conversation
claude --context oauth-implementation "I need to implement OAuth2"

# Continue in same context (remembers previous messages)
claude --context oauth-implementation "What grant types should I support?"

claude --context oauth-implementation "Show me the token refresh flow"

# Each context maintains its own conversation history
```

---

## Directory Structure

```
/ai/
├── claude/
│   ├── context/
│   │   └── .secrets.age
│   └── history/
│       ├── default/
│       │   ├── conversation.jsonl
│       │   └── metadata.json
│       ├── project-auth/
│       │   ├── conversation.jsonl
│       │   └── metadata.json
│       ├── research-ai/
│       └── .current              # Tracks active context
├── grok/
│   └── history/                  # Same structure
├── gemini/
│   └── history/                  # Same structure
└── shared/
    └── agent-messages/           # Agent-to-agent communication (Phase 5)
```

---

## Conversation Format

### conversation.jsonl
Each message appended as JSON line:
```json
{"role": "user", "content": "Hello", "timestamp": "2025-11-13T10:30:00"}
{"role": "assistant", "content": "Hi there!", "timestamp": "2025-11-13T10:30:02"}
```

### metadata.json
Context information:
```json
{
  "name": "project-auth",
  "created": "2025-11-13T10:00:00",
  "last_used": "2025-11-13T10:30:00",
  "message_count": 24
}
```

---

## Workflow Examples

### Software Development Workflow

```bash
# Requirements phase
claude --context myapp-requirements "I need to build a user authentication system"
claude --context myapp-requirements "It should support OAuth and JWT"

# Design phase
claude --context myapp-design "Design the authentication architecture"
claude --context myapp-design "What database schema do I need?"

# Implementation phase
claude --context myapp-impl "Show me the OAuth controller code"

# Review phase
grok --context myapp-review "Review this authentication code for security"

# Testing phase
gemini --context myapp-tests "Generate test cases for OAuth flow"
```

### Research Workflow

```bash
# Research on AI agents
claude --context research-ai-agents "What are the latest multi-agent frameworks?"

# Research on LLMs
grok --context research-llms "What's new in open-source LLMs?"

# Each topic maintains its own conversation history
```

### Topic-Specific Learning

```bash
# Learning Kubernetes
claude --context learn-k8s "Explain Kubernetes pods"
claude --context learn-k8s "Now explain services"
claude --context learn-k8s "How do they work together?"

# Learning Rust (separate conversation)
grok --context learn-rust "Explain Rust ownership"
grok --context learn-rust "What about borrowing?"
```

---

## Features

### Context History Limit
- Default: Last 10 messages loaded (configurable in Python scripts)
- Prevents token limit issues
- Maintains relevant conversation context

### Automatic Context Tracking
- `.current` file tracks active context per agent
- Default context: `default`
- Persists across container restarts

### Metadata Tracking
- Creation timestamp
- Last used timestamp
- Message count
- Easy to extend with tags, descriptions, etc.

---

## Advanced Usage

### Inside Containers

```bash
# Exec into container
sudo podman exec -it claude-agent bash

# Use CLI directly
./claude-chat "Hello"
./claude-chat --list
./claude-chat --context myproject "Let's discuss the API"

# Run Python scripts directly
python3 /home/agent/claude-api.py --help
```

### Programmatic Access

```python
# From within container
from claude_api import chat, list_contexts, ensure_context_exists

# Create new context
ensure_context_exists("my-project")

# Send message
response = chat("Explain async/await", context_name="my-project")
print(response)

# List all contexts
list_contexts()
```

---

## Troubleshooting

### "Cannot decrypt token/key"
```bash
# Verify credentials exist
ls -la /ai/claude/context/.secrets.age

# Re-encrypt if needed
echo 'YOUR_TOKEN' | age -r $(grep "public key:" ~/.age-key.txt | awk '{print $NF}') \
  -o /ai/claude/context/.secrets.age
sudo chmod 600 /ai/claude/context/.secrets.age
```

### "API call failed"
- Check internet connectivity in container: `sudo podman exec claude-agent ping -c 3 8.8.8.8`
- Verify credentials are current (not expired)
- Check API status pages

### Context not found
```bash
# List available contexts
claude --list

# Create new context by using it
claude --context newproject "Hello"
```

### History not persisting
```bash
# Check permissions
ls -la /ai/claude/history/

# Should be owned by your user:aiagent
# If not:
sudo chown -R $USER:aiagent /ai/*/history
```

---

## Performance

- **API latency**: ~1-3 seconds per request (network dependent)
- **History loading**: <50ms for 10-20 messages
- **Storage**: ~1KB per message (JSON)
- **Token usage**: Only recent messages sent to API (configurable limit)

---

## Next: Phase 5

**Agent Orchestration & Collaboration:**
- Agent-to-agent communication
- Workflow engine (multi-agent workflows)
- Task delegation and routing
- Meta-agent conductor

See: `docs/phase5-orchestration.md` (coming soon)

---

## Document Info

- **Version:** 1.0
- **Date:** November 13, 2025
- **Status:** Phase 4 Complete
- **Dependencies:** Phase 1-3

---
