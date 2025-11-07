# Age: Simple File Encryption for AI Credentials

**Age** is a simple, modern file encryption tool. Perfect for securing AI credentials in containers.

---

## Installation (Ubuntu/Debian)

```bash
# Install age
sudo apt update && sudo apt install age -y

# Verify installation
age --version
```

---

## Setup (5 minutes)

### 1. Generate Key Pair

```bash
# Generate your encryption key
age-keygen -o ~/.age-key.txt

# View your public key
grep "public key:" ~/.age-key.txt
```

**Output:**
```
Public key: age1xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### 2. Secure Your Private Key

```bash
# Set restrictive permissions
chmod 600 ~/.age-key.txt

# Backup to secure location (USB drive, password manager, etc.)
cat ~/.age-key.txt
# Copy this somewhere safe!
```

---

## Basic Usage

### Encrypt a File

```bash
# Encrypt credentials file
age -r age1xxxxxxxxxx... -o secrets.age secrets.txt

# The encrypted file (secrets.age) is safe to store anywhere
```

### Decrypt a File

```bash
# Decrypt using your private key
age -d -i ~/.age-key.txt secrets.age > secrets.txt
```

---

## Container Usage

### Copy Key to Container

```bash
# Copy your age key to AI container
sudo podman cp ~/.age-key.txt claude-agent:/home/agent/.age-key.txt
sudo podman exec claude-agent chmod 600 /home/agent/.age-key.txt
```

### Encrypt/Decrypt in Container

```bash
# Inside container
sudo podman exec -it claude-agent bash

# Encrypt
age -r age1xxxxx... -o /ai/claude/context/secrets.age /ai/claude/context/secrets.txt

# Decrypt
age -d -i /home/agent/.age-key.txt /ai/claude/context/secrets.age
```

---

## Quick Reference

| Task | Command |
|------|---------|
| Generate key | `age-keygen -o ~/.age-key.txt` |
| View public key | `grep "public key:" ~/.age-key.txt` |
| Encrypt | `age -r PUBLIC_KEY -o output.age input.txt` |
| Decrypt | `age -d -i ~/.age-key.txt input.age > output.txt` |
| Encrypt stdin | `echo "secret" \| age -r PUBLIC_KEY > secret.age` |
| Decrypt to stdout | `age -d -i ~/.age-key.txt secret.age` |

---

## Security Notes

- ✅ **Never commit** `.age-key.txt` to git
- ✅ **Always use** `chmod 600` on private keys
- ✅ **Backup** your private key securely (you can't decrypt without it!)
- ✅ **Public key** can be shared safely (it only encrypts, can't decrypt)
- ❌ **Don't share** private key or store in plaintext in containers

---

## Troubleshooting

**"age: command not found"**
```bash
sudo apt install age -y
```

**"permission denied: .age-key.txt"**
```bash
chmod 600 ~/.age-key.txt
```

**Lost your key?**
- Restore from backup (USB, password manager)
- If no backup exists, encrypted files are unrecoverable

---

## Alternative: Password-Based Encryption

If you don't want to manage keys, use passphrase mode:

```bash
# Encrypt with password
age -p -o secrets.age secrets.txt
# (prompts for password)

# Decrypt with password
age -d secrets.age > secrets.txt
# (prompts for password)
```

⚠️ **Less secure than key-based** (vulnerable to weak passwords)

---

## Links

- [Age GitHub](https://github.com/FiloSottile/age)
- [Age Documentation](https://age-encryption.org)

---

**Setup time:** 2 minutes  
**Skill level:** Beginner-friendly  
**Use case:** Encrypting AI credentials in `/ai/{model}/context/`
