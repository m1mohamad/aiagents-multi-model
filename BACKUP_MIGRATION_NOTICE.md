# 🔒 Backup System Migration Notice

## ⚠️ IMPORTANT: Backup System Has Been Updated

The backup system has been upgraded to use **encrypted backups** for better security.

---

## What Changed?

### Old Backup System (Deprecated):
- **Location**: `/tmp/ai-backups/`
- **Format**: Unencrypted directories
- **Security**: ❌ Conversations in plain text
- **Module**: `BackupManager` (from `backup_legacy.py`)

### New Backup System (Active):
- **Location**: `~/ai-backups/`
- **Format**: Encrypted `.tar.gz.age` files
- **Security**: ✅ Everything encrypted with age
- **Module**: `SecureBackupManager` (from `backup.py`)

---

## Migration Steps

### 1. Check for Old Backups:
```bash
ls -la /tmp/ai-backups/
```

### 2. Create New Secure Backup:
```bash
# Using Makefile (will be added in next commit)
make py-backup-secure

# Or using Python directly
sudo python3 -c "
from ai_agents.deployment import SecureBackupManager
mgr = SecureBackupManager()
backup_path = mgr.create_backup()
print(f'Backup created: {backup_path}')
"
```

### 3. Verify New Backup:
```bash
ls -la ~/ai-backups/
```

### 4. Delete Old Backups (Optional):
```bash
# After verifying new backup works
sudo rm -rf /tmp/ai-backups/
```

---

## Python Code Changes

### Old Code (Still Works, But Deprecated):
```python
from ai_agents.deployment import BackupManager

mgr = BackupManager()
backup_path = mgr.create_backup()  # ❌ Unencrypted!
```

### New Code (Recommended):
```python
from ai_agents.deployment import SecureBackupManager

mgr = SecureBackupManager()
backup_path = mgr.create_backup()  # ✅ Encrypted!
```

---

## Makefile Commands

### Old Commands (Still Work):
```bash
make backup          # Creates tar.gz backup (unencrypted)
make py-backup       # Uses old BackupManager (unencrypted)
```

### New Commands (Will Be Added):
```bash
make py-backup-secure         # Create encrypted backup
make py-list-backups-secure   # List encrypted backups
make py-restore-secure        # Restore from encrypted backup
```

---

## What's Next?

The next commits will add:
1. **Commit 2**: Secure backup commands to deploy-cli.py
2. **Commit 3**: Makefile targets for secure backups
3. **Commit 4**: Comprehensive tests

---

## Why This Change?

### Security Issues with Old System:
- ❌ Conversation history stored in plain text
- ❌ Backups in world-readable /tmp directory
- ❌ No validation after backup
- ❌ No verification that backups work

### Benefits of New System:
- ✅ Everything encrypted with age
- ✅ Secure location (~/ai-backups)
- ✅ Automatic validation after backup
- ✅ Safety backup before restore
- ✅ Dry-run support
- ✅ Age key validation

---

## Backward Compatibility

The old `BackupManager` is still available for backward compatibility:

```python
# Still works (but deprecated)
from ai_agents.deployment import BackupManager
```

**Warning**: Old backups are NOT encrypted. For security, use `SecureBackupManager`.

---

## Questions?

Read the full documentation:
- `BACKUP_IMPROVEMENTS.md` - Detailed security improvements
- `SECURE_DEPLOYMENT_PLAN.md` - Complete deployment plan (11 commits)

---

## Status

**Current Phase**: Week 1, Commit 1 ✅
**Next**: Add secure backup commands to CLI
