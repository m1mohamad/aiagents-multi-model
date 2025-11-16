# Claude API Key Setup Guide

**How to get and configure Claude API keys for the CLI**

---

## Overview

The Claude CLI uses the **official Anthropic API** with API keys. This is the production-ready, reliable approach that bypasses Cloudflare bot protection issues.

### Why API Keys?

- ✅ **Reliable** - No Cloudflare blocking
- ✅ **Production-ready** - Official, supported method
- ✅ **Scalable** - Handles high request volumes
- ✅ **Programmatic** - Designed for automation

---

## Getting Your API Key

### Step 1: Create Anthropic Account

1. Go to: https://console.anthropic.com/
2. Sign up or log in
3. Navigate to **Settings → API Keys**

### Step 2: Create API Key

1. Click **"Create Key"**
2. Give it a name (e.g., "AI Multi-Agent CLI")
3. Copy the key - starts with `sk-ant-api03-`

**⚠️ Important:** Save this key immediately - you won't be able to see it again!

---

## Encrypting and Storing the Key

### Encrypt with Age

```bash
# Encrypt your API key
echo "sk-ant-api03-YOUR_API_KEY_HERE" | \
  age -r $(grep "public key:" ~/.age-key.txt | awk '{print $NF}') \
  -o /ai/claude/context/.secrets.age

# Fix permissions
sudo chmod 600 /ai/claude/context/.secrets.age
```

### Verify Encryption

```bash
# Test decryption (should show your API key)
age -d -i ~/.age-key.txt /ai/claude/context/.secrets.age
```

---

## Cost Information

### Pricing (Claude Sonnet 4)

| Type | Cost | Details |
|------|------|---------|
| **Input tokens** | $3 per million tokens | Text you send to Claude |
| **Output tokens** | $15 per million tokens | Text Claude sends back |
| **Model** | claude-sonnet-4-20250514 | Latest production model |

### Estimated Monthly Costs

**Light Usage:**
- ~50 queries/day
- Average 500 tokens input + 1000 tokens output per query
- **Cost:** ~$3-5/month

**Moderate Usage:**
- ~100 queries/day
- Average 1000 tokens input + 2000 tokens output per query
- **Cost:** ~$10-15/month

**Heavy Usage:**
- ~500 queries/day
- Average 2000 tokens input + 4000 tokens output per query
- **Cost:** ~$50-75/month

### Cost Management Tips

1. **Use contexts wisely** - Separate topics reduce repeated context
2. **Limit history** - Default 10 messages keeps costs down
3. **Monitor usage** - Check console.anthropic.com regularly
4. **Set budget alerts** - Configure in Anthropic Console

---

## API Key vs Session Token

| Feature | API Key (Current) | Session Token (Blocked) |
|---------|-------------------|------------------------|
| **Reliability** | ✅ High | ❌ Blocked by Cloudflare |
| **Cost** | Pay-per-use ($3-15/M tokens) | Free with Pro subscription |
| **Setup** | Get from console.anthropic.com | Extract from browser |
| **Production** | ✅ Yes | ❌ No (unreliable) |
| **Support** | ✅ Official | ❌ Unsupported |

**Decision:** We use API keys because session-based auth is blocked by Cloudflare's bot protection, making it unreliable for production use.

---

## Configuration After Getting Key

### 1. Encrypt and Store

```bash
# Store your API key
echo "sk-ant-api03-YOUR_KEY" | \
  age -r $(grep "public key:" ~/.age-key.txt | awk '{print $NF}') \
  -o /ai/claude/context/.secrets.age

sudo chmod 600 /ai/claude/context/.secrets.age
```

### 2. Deploy/Reconfigure

```bash
# If first time
make config

# If updating existing setup
make reconfigure
```

### 3. Test

```bash
# Basic test
claude "Hello, how are you?"

# Context test
claude --context test "This is a test"

# List contexts
claude --list
```

---

## API Key Security

### Best Practices

✅ **Do:**
- Store encrypted with age (256-bit)
- Use file permissions 600 (owner read/write only)
- Rotate keys every 3-6 months
- Monitor usage in Anthropic Console
- Keep backup of age key in secure location

❌ **Don't:**
- Commit API keys to git
- Share keys in plain text
- Use same key across multiple systems
- Store in unencrypted files

### Key Rotation

```bash
# 1. Create new key in Anthropic Console
# 2. Encrypt new key
echo "NEW_API_KEY" | age -r $(grep "public key:" ~/.age-key.txt | awk '{print $NF}') \
  -o /ai/claude/context/.secrets.age

# 3. Test
claude "Test message"

# 4. Delete old key from Anthropic Console
```

---

## Troubleshooting

### "Error: Cannot decrypt API key"

**Cause:** Age key not found or wrong permissions

**Fix:**
```bash
# Verify age key exists
ls -la ~/.age-key.txt

# Should be: -rw------- (600)
# If not: chmod 600 ~/.age-key.txt
```

### "Error calling Claude API: 401"

**Cause:** Invalid API key

**Fix:**
1. Verify key format: starts with `sk-ant-api03-`
2. Check key is active in Anthropic Console
3. Re-encrypt and save if needed

### "Error calling Claude API: 429"

**Cause:** Rate limit exceeded

**Fix:**
- Wait a few minutes
- Check usage in Anthropic Console
- Consider upgrading API tier if needed

### "Error calling Claude API: 400"

**Cause:** Invalid request format

**Fix:**
- Check message content (no empty messages)
- Verify context history is valid
- Check conversation.jsonl for corruption

---

## Rate Limits

### Default Limits (Free Tier)

- **Requests:** 50 per minute
- **Tokens:** 40K per minute (input)
- **Tokens:** 8K per minute (output)

### Paid Tier Limits

- **Requests:** Higher limits available
- **Tokens:** Configurable based on plan
- Contact Anthropic for enterprise limits

### Managing Rate Limits

```bash
# Space out requests if hitting limits
claude "First query"
sleep 2
claude "Second query"
```

---

## Usage Monitoring

### Check Usage in Console

1. Go to: https://console.anthropic.com/
2. Navigate to **Settings → Usage**
3. View:
   - Requests per day/month
   - Token usage (input/output)
   - Cost breakdown
   - Spending trends

### Set Budget Alerts

1. **Settings → Billing**
2. Configure spending limits
3. Set email alerts
4. Monitor regularly

---

## Comparison with Other Services

| Service | Our Usage | Why |
|---------|-----------|-----|
| **Claude** | Official API (paid) | Reliable, production-ready |
| **Grok** | SSO token (free with Premium) | Works, not blocked |
| **Gemini** | Official API (free tier) | Free, designed for programmatic use |

**Each service uses its optimal authentication method.**

---

## Getting Help

### Anthropic Support

- **Documentation:** https://docs.anthropic.com/
- **Discord:** https://discord.gg/anthropic
- **Email:** support@anthropic.com
- **Status:** https://status.anthropic.com/

### Common Issues

1. **High costs?** Reduce max_history parameter
2. **Slow responses?** Normal for complex queries
3. **Need more quota?** Contact Anthropic for upgrade

---

## Next Steps

After setting up API key:

1. ✅ Test basic functionality
2. ✅ Test context switching
3. ✅ Monitor first week's usage
4. ✅ Set budget alerts
5. ✅ Adjust max_history if needed

---

## Document Info

- **Version:** 1.0
- **Date:** November 15, 2025
- **Authentication:** Official Anthropic API
- **Cost:** Pay-per-use (see pricing above)

---
