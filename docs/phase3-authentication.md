# Phase 3: Authentication & CLI Setup

**Configure secure authentication for Claude, Grok, and Gemini CLI access**

---

## Quick Start

```bash
cd /home/aiagent/ai-setup
sudo bash setup-phase3.sh
```

**If credentials don't exist yet, the script will show you how to add them manually with encryption commands.**

**Time:** 2 minutes (if credentials already configured)

---

## What Phase 3 Does

1. ✅ Installs `age` encryption (host + containers)
2. ✅ Generates encryption key (if needed)
3. ✅ Fixes container permissions
4. ✅ Checks for existing credentials
5. ✅ Installs CLI wrappers (claude-chat, grok-chat, gemini-chat)
6. ✅ Tests decryption works

---

## Adding Credentials Manually

If you need to add credentials after running the script:

```bash
# Get your public key
grep "public key:" ~/.age-key.txt

# Encrypt Claude token
echo "YOUR_CLAUDE_TOKEN" | age -r age1YOUR_KEY... -o /ai/claude/context/.secrets.age
chmod 600 /ai/claude/context/.secrets.age

# Encrypt Grok SSO token
echo "YOUR_GROK_TOKEN" | age -r age1YOUR_KEY... -o /ai/grok/context/.secrets.age
chmod 600 /ai/grok/context/.secrets.age

# Encrypt Gemini API key
echo "YOUR_GEMINI_KEY" | age -r age1YOUR_KEY... -o /ai/gemini/context/.secrets.age
chmod 600 /ai/gemini/context/.secrets.age
```

**Then run the setup script again to install wrappers.**

---

## Usage

```bash
# Access containers
sudo podman exec -it claude-agent bash
sudo podman exec -it grok-agent bash
sudo podman exec -it gemini-agent bash

# Use CLI wrappers
./claude-chat "Hello"
./grok-chat "Hello"
./gemini-chat "What is AI?"  # <- This one actually works!
```

---

## How to Get Tokens

### Claude (claude.ai)
1. Login to https://claude.ai
2. F12 → Application → Cookies → sessionKey
3. Copy value (starts with `sk-ant-sid01-`)

### Grok (x.ai)
1. Login to https://x.ai
2. F12 → Application → Cookies → sso
3. Copy value (JWT token)

### Gemini (Google AI Studio)
1. Go to https://aistudio.google.com/app/apikey
2. Create API key
3. Copy value (starts with `AIza`)

---

## Files Created

```
/ai/
├── claude/context/.secrets.age    # Encrypted credentials
├── grok/context/.secrets.age
└── gemini/context/.secrets.age

Containers:
├── /home/agent/claude-chat        # CLI wrapper
├── /home/agent/grok-chat
└── /home/agent/gemini-chat
```

---

## Troubleshooting

**"Cannot decrypt token"**
```bash
# Verify age key exists in container
sudo podman exec claude-agent ls -la /home/agent/.age-key.txt
# Should show: -rw------- 1 mo ...

# If permission denied, fix with:
sudo podman exec -u root claude-agent chmod 755 /home/agent
```

**"API call failed"**
- Check internet connection in container
- Verify token is current (not expired)
- Re-extract token from browser

---

## Next: Phase 4

**Context Persistence & Conversation Management**
- Save conversation history to `/ai/{model}/history/`
- Load previous context automatically
- Multi-turn conversations
- Agent orchestration (Claude → Grok → Gemini workflows)

---

## Document Info

- **Version:** 1.1 (Fixed)
- **Date:** November 4, 2025
- **Status:** Phase 3 Complete
- **Dependencies:** Phase 2, age installed

---
