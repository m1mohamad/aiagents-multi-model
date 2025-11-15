# Claude Session-Based Authentication

**How the Claude CLI uses your Claude Pro subscription instead of API keys**

---

## Overview

The Claude CLI implementation uses **session-based authentication** from your Claude Pro browser session, allowing you to use your existing subscription without paying for separate API access.

### Why Session-Based?

- ✅ **No extra cost** - Use your existing Claude Pro subscription
- ✅ **Same features** - Access to Claude Sonnet 4 and all Pro features
- ✅ **Simple setup** - Just extract sessionKey from browser cookies
- ✅ **No API limits** - Subject to your Pro plan limits, not separate API quotas

### vs API Key Approach

| Feature | Session-Based (Our Approach) | API Key (Official SDK) |
|---------|------------------------------|------------------------|
| Cost | Included in Pro subscription | Separate API billing |
| Setup | Extract browser cookie | Create API key |
| Models | Claude Sonnet 4 (Pro) | Same models available |
| Rate Limits | Pro plan limits | API-specific limits |
| Authentication | sessionKey cookie | API key header |

---

## How It Works

### 1. Session Token Extraction

When you log into claude.ai, your browser stores a session token:

```
Cookie: sessionKey=sk-ant-sid01-...
```

This token authenticates you to Claude's web API.

### 2. API Endpoints

Instead of using `api.anthropic.com` (official API), we use `claude.ai/api`:

```python
# Official API (requires paid API key)
POST https://api.anthropic.com/v1/messages
Authorization: x-api-key YOUR_API_KEY

# Session API (uses Pro subscription)
POST https://claude.ai/api/organizations/{org_id}/chat_conversations/{conv_id}/completion
Cookie: sessionKey=YOUR_SESSION_KEY
```

### 3. Conversation Management

Each context in our CLI maps to a conversation in Claude.ai:

```
/ai/claude/history/
  ├── default/
  │   ├── conversation_uuid.txt  # Maps to claude.ai conversation
  │   └── conversation.jsonl     # Local backup
  ├── project-auth/
  │   ├── conversation_uuid.txt
  │   └── conversation.jsonl
```

### 4. Server-Sent Events (SSE)

Claude's web API uses SSE for streaming responses:

```python
response = requests.post(..., stream=True)
for line in response.iter_lines():
    if line.startswith('data: '):
        data = json.loads(line[6:])
        # Extract completion text
```

---

## Implementation Details

### Key Functions

#### 1. Get Organization ID

```python
def get_organization_id(session_token):
    response = requests.get(
        "https://claude.ai/api/organizations",
        headers={"Cookie": f"sessionKey={session_token}"}
    )
    return response.json()[0]['uuid']
```

Every Claude account has an organization ID needed for API calls.

#### 2. Create/Get Conversation

```python
def get_or_create_conversation(session_token, org_id, context_name):
    # Check if we have saved conversation UUID
    if conversation_uuid_exists:
        return saved_uuid

    # Create new conversation
    response = requests.post(
        f"https://claude.ai/api/organizations/{org_id}/chat_conversations",
        json={"name": f"Context: {context_name}", "uuid": str(uuid.uuid4())}
    )
    return response.json()['uuid']
```

Each CLI context gets its own Claude.ai conversation for continuity.

#### 3. Send Message

```python
def send_message_to_claude(session_token, org_id, conversation_uuid, message):
    response = requests.post(
        f"https://claude.ai/api/organizations/{org_id}/chat_conversations/{conversation_uuid}/completion",
        headers={
            "Cookie": f"sessionKey={session_token}",
            "Accept": "text/event-stream"
        },
        json={"prompt": message, "timezone": "UTC"},
        stream=True
    )

    # Parse SSE stream for response
    for line in response.iter_lines():
        # Extract completion text
```

Sends message and parses streaming response.

---

## Session Token Lifecycle

### Extraction

From Chrome/Firefox/Brave:
1. Open claude.ai and log in
2. Press F12 (Developer Tools)
3. Go to Application → Cookies → https://claude.ai
4. Find `sessionKey` cookie
5. Copy the value (starts with `sk-ant-sid01-`)

### Storage

```bash
# Encrypt with age
echo 'sk-ant-sid01-YOUR_TOKEN' | age -r $(grep "public key:" ~/.age-key.txt | awk '{print $NF}') \
  -o /ai/claude/context/.secrets.age
```

### Expiration

Session tokens typically last:
- **Active use:** Months (refreshed automatically)
- **Inactive:** ~30 days
- **Security events:** Immediate (password change, logout all devices)

### Renewal

If you get "Session expired" errors:
1. Re-extract sessionKey from browser
2. Re-encrypt and save
3. Continue using CLI

No need to reconfigure anything else.

---

## Security Considerations

### What's Stored

- ✅ Session token encrypted at rest (age 256-bit)
- ✅ Conversation UUIDs (not sensitive)
- ✅ Local conversation history (your messages)
- ❌ Password (never stored)

### Permissions

Session token has same permissions as your browser:
- Access to all Claude Pro features
- Read/write conversations
- Manage account settings

**Best Practice:** Treat session token like a password.

### Token Rotation

Recommended:
- Rotate every 30-90 days
- Rotate after suspicious activity
- Rotate if shared accidentally

How to rotate:
```bash
# 1. Logout from Claude.ai in browser
# 2. Login again
# 3. Extract new sessionKey
# 4. Re-encrypt and save
echo 'NEW_TOKEN' | age -r $(grep "public key:" ~/.age-key.txt | awk '{print $NF}') \
  -o /ai/claude/context/.secrets.age
```

---

## Advantages Over Official API

### Cost Savings

**Scenario:** 100 messages/day, 30 days/month

| Approach | Monthly Cost |
|----------|-------------|
| Session-based (Pro subscription) | $20 (Pro plan) |
| API with similar usage | $20 (Pro) + $50-100 (API usage) |

### Feature Parity

Both approaches access the same model (Claude Sonnet 4), but:
- Session-based: Included in Pro subscription
- API: Separate billing at ~$3/$15 per million tokens

### Rate Limits

**Pro Subscription (Session):**
- Subject to Pro plan fair use
- Typically 40-50 messages per 5 hours
- Shared with browser usage

**API:**
- Separate rate limits
- Based on API tier
- Not shared with browser

---

## Troubleshooting

### "Session token expired"

**Cause:** Token no longer valid
**Fix:** Re-extract from browser and re-encrypt

### "No organizations found"

**Cause:** Account issue or token invalid
**Fix:** Verify you're logged into claude.ai, then re-extract token

### "401 Unauthorized"

**Cause:** Invalid or malformed session token
**Fix:**
1. Check token format (should start with `sk-ant-sid01-`)
2. Ensure no extra spaces or newlines
3. Re-extract and re-encrypt

### "Timeout after 120 seconds"

**Cause:** Long response generation
**Fix:** This is expected for complex queries, response should still save

---

## Comparison with Other Agents

| Agent | Authentication Method | Why |
|-------|----------------------|-----|
| **Claude** | Session token | Use Pro subscription, no API costs |
| **Grok** | SSO token | Similar to Claude, uses X Premium subscription |
| **Gemini** | API key | Free API available, designed for programmatic access |

All three approaches work and are well-suited to each platform's model.

---

## Future Enhancements

Potential improvements to session-based auth:

1. **Auto-refresh:** Detect expiration and prompt for new token
2. **Multiple accounts:** Support switching between Claude accounts
3. **Session health check:** Periodic validation of token status
4. **Conversation sync:** Download existing claude.ai conversations

---

## References

### API Endpoints

```
GET  /api/organizations
POST /api/organizations/{org_id}/chat_conversations
POST /api/organizations/{org_id}/chat_conversations/{uuid}/completion
GET  /api/organizations/{org_id}/chat_conversations/{uuid}
```

### Headers Required

```
Cookie: sessionKey={session_token}
User-Agent: Mozilla/5.0 ...
Content-Type: application/json
Accept: text/event-stream (for streaming)
```

### Response Format

Server-Sent Events (SSE):
```
data: {"type":"content_block_start","content_block":{"type":"text","text":""}}
data: {"type":"content_block_delta","delta":{"type":"text_delta","text":"Hello"}}
data: {"type":"content_block_delta","delta":{"type":"text_delta","text":" world"}}
data: {"type":"content_block_stop"}
data: {"type":"message_stop"}
```

---

## Document Info

- **Version:** 1.0
- **Date:** November 13, 2025
- **Status:** Production Implementation
- **File:** `scripts/claude-api.py`

---
