# Token Extraction Guide
## Getting Authentication Credentials for Claude, Grok, and Gemini

**Time Required:** 10-15 minutes total  
**Prerequisites:** Active accounts with Claude.ai, X.ai (Grok), and Google AI Studio

---

## Overview

Each AI service requires authentication credentials:
- **Claude:** Session key (cookie-based)
- **Grok:** SSO token (cookie-based)
- **Gemini:** API key (developer portal)

All credentials will be encrypted with age before storage.

---

## Claude Session Key Extraction

### Prerequisites
- Active Claude.ai subscription (Pro or Team)
- Browser with Developer Tools (Chrome, Firefox, Brave, Edge)

### Method 1: Browser Cookies (Recommended)

#### Chrome / Brave / Edge

1. **Open Claude.ai**
   ```
   Navigate to: https://claude.ai
   Login to your account
   ```

2. **Open Developer Tools**
   ```
   Press F12
   Or right-click → Inspect
   ```

3. **Navigate to Application Tab**
   ```
   Top menu: Elements | Console | Sources | Network | Performance | Memory | Application
   Click "Application"
   ```

4. **Access Cookies**
   ```
   Left sidebar:
   Storage
     └── Cookies
           └── https://claude.ai
   
   Click on "https://claude.ai"
   ```

5. **Find sessionKey**
   ```
   Look for cookie named: sessionKey
   
   It will look like:
   Name: sessionKey
   Value: sk-ant-sid01-tgNvSmeq3E7i27YiHyTaddG4RKwTQx0Nc0IYNA...
   ```

6. **Copy the Value**
   ```
   Click on the Value field
   Copy entire string (starts with sk-ant-sid01-)
   Typical length: ~150+ characters
   ```

#### Firefox

1. **Open Claude.ai and login**

2. **Open Developer Tools**
   ```
   Press F12
   Or Menu → More Tools → Web Developer Tools
   ```

3. **Go to Storage Tab**
   ```
   Top menu: Inspector | Console | Debugger | Style Editor | Performance | Memory | Storage
   Click "Storage"
   ```

4. **Navigate to Cookies**
   ```
   Left sidebar:
   Storage
     └── Cookies
           └── https://claude.ai
   ```

5. **Find and Copy sessionKey**
   ```
   Look for: sessionKey
   Copy the entire Value
   ```

### Method 2: Network Request (Alternative)

1. **Open DevTools → Network tab**
2. **Send a message to Claude**
3. **Find any API request** (look for requests to claude.ai/api/)
4. **Click request → Headers**
5. **Find Cookie header**
6. **Copy sessionKey value** from Cookie header

### Security Notes

- ⚠️ **Never share this token** - it gives full access to your Claude account
- ⏰ **Token expires** after ~30 days
- 🔄 **Rotate if compromised** by logging out and back in
- 🧹 **Clear after copying** (close DevTools, clear clipboard)

---

## Grok SSO Token Extraction

### Prerequisites
- X.ai account with Grok access
- Browser with Developer Tools

### Step-by-Step

1. **Open X.ai**
   ```
   Navigate to: https://x.ai
   Or: https://grok.x.ai
   Login to your account
   ```

2. **Open Developer Tools**
   ```
   Press F12
   ```

3. **Go to Application/Storage Tab**
   ```
   Chrome/Edge/Brave: Application tab
   Firefox: Storage tab
   ```

4. **Access Cookies**
   ```
   Left sidebar:
   Cookies
     └── https://x.ai (or https://grok.x.ai)
   ```

5. **Find SSO Token**
   ```
   Look for cookie named: sso
   (May also be named: sso-rw)
   
   Value will be a JWT token:
   eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzZXNzaW9uX2lkIjoiZTg3YzFlYmMtY2Q...
   ```

6. **Copy the Value**
   ```
   Copy entire JWT string
   Starts with: eyJ
   Typical length: ~200+ characters
   ```

### Alternative Method: Ask Grok

If you have trouble finding the token:

1. **Ask Grok directly:**
   ```
   "What cookies does your web interface use for authentication?"
   ```

2. **Grok will guide you** to the correct cookie name

### Verification

Your SSO token should:
- Start with `eyJ` (base64-encoded JWT)
- Contain two dots (`.`) separating three parts
- Be 150-300 characters long

### Security Notes

- ⚠️ **JWT tokens are sensitive** - treat like a password
- ⏰ **Expiration varies** - based on X.ai policy
- 🔄 **Refresh by re-login** if expired

---

## Gemini API Key Creation

### Prerequisites
- Google account
- Access to Google AI Studio

### Step-by-Step

1. **Open Google AI Studio**
   ```
   Navigate to: https://aistudio.google.com/app/apikey
   Or: https://makersuite.google.com/app/apikey
   ```

2. **Sign In**
   ```
   Use your Google account
   Complete any 2FA if required
   ```

3. **Create API Key**
   ```
   Click: "Create API Key" button
   
   Options:
   - Create new project (recommended for isolation)
   - Use existing project
   ```

4. **Copy API Key**
   ```
   Key will be displayed once:
   YOUR_GEMINI_API_KEY_HERE

   Format: AIza... (starts with AIza)
   Length: ~40 characters
   ```

5. **Save Immediately**
   ```
   ⚠️ KEY SHOWN ONLY ONCE!
   Copy and save before closing dialog
   ```

### API Key Features

**Free Tier Includes:**
- 15 requests per minute
- 1,500 requests per day
- 1 million requests per month
- Gemini 2.5 Flash access

**Models Available:**
- gemini-2.5-flash (fast, cheap)
- gemini-2.5-pro (powerful)
- gemini-2.0-flash (alternative)

### Security Notes

- ⚠️ **API key visible only once** during creation
- 🔒 **Restrict by IP** (optional, in API settings)
- 🔄 **Rotate periodically** (delete old, create new)
- 📊 **Monitor usage** at console.cloud.google.com

---

## Encrypting Credentials

### After Extraction

Once you have all tokens, encrypt them:

```bash
# Get your age public key
grep "public key:" ~/.age-key.txt

# Encrypt Claude token
echo "sk-ant-sid01-YOUR_TOKEN" | age -r age1YOUR_PUBLIC_KEY -o /ai/claude/context/.secrets.age
chmod 600 /ai/claude/context/.secrets.age

# Encrypt Grok token  
echo "eyJ0eXAiOiJKV1QiLCJh..." | age -r age1YOUR_PUBLIC_KEY -o /ai/grok/context/.secrets.age
chmod 600 /ai/grok/context/.secrets.age

# Encrypt Gemini key
echo "AIzaSyDv9aqfheAHII..." | age -r age1YOUR_PUBLIC_KEY -o /ai/gemini/context/.secrets.age
chmod 600 /ai/gemini/context/.secrets.age
```

### Verification

Test decryption:

```bash
# Should return your tokens
sudo podman exec claude-agent age -d -i /home/agent/.age-key.txt /ai/claude/context/.secrets.age
sudo podman exec grok-agent age -d -i /home/agent/.age-key.txt /ai/grok/context/.secrets.age
sudo podman exec gemini-agent age -d -i /home/agent/.age-key.txt /ai/gemini/context/.secrets.age
```

---

## Troubleshooting

### Claude: Can't Find sessionKey

**Problem:** Cookie not visible in DevTools

**Solutions:**
1. **Ensure you're logged in** - Visit claude.ai first
2. **Check correct domain** - Must be claude.ai, not anthropic.com
3. **Try incognito mode** - Fresh login session
4. **Clear cache** - Sometimes old cookies hide new ones
5. **Try Network method** - Inspect actual API requests

### Grok: Multiple SSO Cookies

**Problem:** See both `sso` and `sso-rw`

**Solution:** Both have identical values, use either one

### Gemini: API Key Already Created

**Problem:** "API key already exists" error

**Solutions:**
1. **Find existing key** - Check API Keys page
2. **Regenerate** - Delete old, create new
3. **Use different project** - Create new Google Cloud project

### General: Token Expired

**Problem:** API returns 401/403 errors

**Solutions:**
1. **Re-extract token** from browser (login again)
2. **Check token format** (correct prefix: sk-ant-, eyJ, AIza)
3. **Verify encryption** (decrypt test)
4. **Check permissions** (600 on .secrets.age files)

---

## Token Management Best Practices

### Storage
- ✅ **Always encrypt** with age before storing
- ✅ **Use 600 permissions** on encrypted files
- ✅ **Backup age private key** to secure location
- ❌ **Never commit** tokens to git
- ❌ **Never share** in plaintext

### Rotation Schedule
- **Claude:** Every 30 days (or on expiry)
- **Grok:** When notified or on logout
- **Gemini:** Every 90 days (best practice)

### Monitoring
- Check token validity weekly
- Monitor for unusual API usage
- Revoke immediately if compromised

### Team Sharing
- ❌ **Never share tokens** between team members
- ✅ **Each person extracts own** tokens
- ✅ **Each person has own** age key
- ✅ **Each person deploys** independently

---

## Quick Reference Card

| Service | Token Type | Where to Find | Starts With | Length |
|---------|------------|---------------|-------------|---------|
| Claude | Session Key | DevTools → Application → Cookies → sessionKey | `sk-ant-sid01-` | ~150+ chars |
| Grok | SSO Token | DevTools → Application → Cookies → sso | `eyJ` | ~200+ chars |
| Gemini | API Key | aistudio.google.com/app/apikey | `AIza` | ~40 chars |

---

## Security Checklist

Before continuing:
- [ ] Tokens extracted from legitimate sources
- [ ] Tokens tested (made test API call)
- [ ] Age key generated and backed up
- [ ] Tokens encrypted with age
- [ ] .secrets.age files have 600 permissions
- [ ] DevTools closed after extraction
- [ ] Clipboard cleared
- [ ] Browser cache cleared (optional but recommended)

---

## Next Steps

After extracting and encrypting all tokens:

1. **Verify encryption:**
   ```bash
   sudo bash scripts/setup-phase3.sh
   ```

2. **Test APIs:**
   ```bash
   sudo podman exec gemini-agent /home/agent/gemini-chat "Test"
   ```

3. **Ready to use!**

---

## Support

**Issues extracting tokens?**
- Check browser compatibility (Chrome/Firefox recommended)
- Ensure JavaScript enabled
- Try different browser
- Contact AI service support if account issues

**Encryption issues?**
- See: docs/age-encryption-guide.md
- Verify age installation: `age --version`
- Check age key: `ls -la ~/.age-key.txt`

---

**Document Version:** 1.0  
**Last Updated:** November 2025  
**Tested On:** Chrome 119+, Firefox 120+, Brave 1.60+
