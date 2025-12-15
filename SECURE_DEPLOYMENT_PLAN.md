# 🔒 Secure Deployment Stabilization Plan

## Current Issues

### 1. Backup Security ❌
- Conversations stored in plain text
- Backups in insecure /tmp location
- No validation after backup
- Only secrets encrypted, not everything

### 2. Secrets Validation ⚠️
- No validation on `make deploy`
- No check if age key exists before operations
- No verification secrets can be decrypted
- No permission checks (600)

### 3. Deployment Reproducibility ⚠️
- Age key may not exist
- Secrets may be corrupted
- No pre-deployment checks
- No post-deployment verification

---

## Solution: 3-Phase Stabilization

### Phase 1: Secure Backup System ✅
**Goal**: Encrypt everything, validate backups

**Implementation:**
1. Replace `backup.py` with `backup_v2.py`
2. Update deployment module exports
3. Add Makefile commands
4. Add validation tests

**Files to modify:**
- `src/ai_agents/deployment/__init__.py` - Export SecureBackupManager
- `scripts/deploy-cli.py` - Add secure backup commands
- `Makefile` - Add py-backup-secure commands
- `tests/deployment/test_backup_v2.py` - Add tests

**New commands:**
```bash
make py-backup-secure         # Create encrypted backup
make py-list-backups-secure   # List encrypted backups
make py-restore-secure        # Restore with validation
```

---

### Phase 2: Secrets Validation 🔧
**Goal**: Validate secrets before/during/after deployment

**Implementation:**
1. Add pre-deployment checks
2. Add post-deployment validation
3. Add healing commands

**Validation checks:**
- ✅ Age key exists at ~/.age-key.txt
- ✅ Age key has 600 permissions
- ✅ Can extract public key
- ✅ All .secrets.age files exist
- ✅ All .secrets.age files have 600 permissions
- ✅ All secrets can be decrypted

**Files to create:**
- `scripts/validate-deployment.sh` - Bash validation
- `src/ai_agents/deployment/validator.py` - Python validation

**New commands:**
```bash
make validate                 # Validate entire deployment
make validate-secrets         # Validate secrets only
make heal-permissions         # Fix file permissions
make heal-secrets             # Re-encrypt secrets if needed
```

---

### Phase 3: Deployment Integration 🔧
**Goal**: Integrate validation into deployment workflow

**Implementation:**
1. Add validation to `make deploy`
2. Add validation to `make config`
3. Add validation to `make reconfigure`
4. Create pre-flight checks

**Workflow:**
```bash
make deploy
  ├─ Pre-flight checks
  │   ├─ Check sudo access
  │   ├─ Check podman installed
  │   └─ Check age installed
  ├─ Run deployment (existing scripts)
  ├─ Post-deployment validation
  │   ├─ Validate containers running
  │   ├─ Validate age key
  │   ├─ Validate secrets
  │   └─ Run health checks
  └─ Create automatic backup
```

---

## Implementation Roadmap

### Week 1: Secure Backup (4 commits)

#### Commit 1: Integrate SecureBackupManager
```bash
feat(backup): Replace backup.py with secure encrypted backup system

- Rename backup.py to backup_legacy.py
- Move backup_v2.py to backup.py
- Update __init__.py exports
- Add deprecation notice for old backups
```

**Files:**
- `src/ai_agents/deployment/backup_legacy.py` (renamed)
- `src/ai_agents/deployment/backup.py` (from backup_v2.py)
- `src/ai_agents/deployment/__init__.py` (update exports)

#### Commit 2: Add secure backup commands to CLI
```bash
feat(cli): Add secure backup commands to deploy-cli.py

- Add backup-secure command
- Add list-backups-secure command
- Add restore-secure command with dry-run
- Add backup validation
```

**Files:**
- `scripts/deploy-cli.py` (add commands)

#### Commit 3: Add secure backup to Makefile
```bash
feat(make): Add secure backup targets to Makefile

- make py-backup-secure
- make py-list-backups-secure
- make py-restore-secure
- Update help text
```

**Files:**
- `Makefile` (add targets)

#### Commit 4: Add secure backup tests
```bash
test(backup): Add comprehensive tests for secure backup

- Test encryption/decryption
- Test validation
- Test safety backups
- Test permission checks
- Test age key validation
```

**Files:**
- `tests/deployment/test_backup_v2.py` (comprehensive tests)

---

### Week 2: Secrets Validation (4 commits)

#### Commit 5: Create deployment validator
```bash
feat(validation): Add deployment validation module

- Create Validator class
- Age key validation
- Secrets validation
- Permission checks
- Decryption tests
```

**Files:**
- `src/ai_agents/deployment/validator.py` (new)
- `tests/deployment/test_validator.py` (new)

#### Commit 6: Add validation commands to CLI
```bash
feat(cli): Add validation commands to deploy-cli.py

- validate command (full system check)
- validate-secrets command
- validate-age-key command
- heal-permissions command
```

**Files:**
- `scripts/deploy-cli.py` (add commands)

#### Commit 7: Add bash validation script
```bash
feat(scripts): Add standalone validation script

- scripts/validate-deployment.sh
- Pre-deployment checks
- Post-deployment validation
- Healing commands
```

**Files:**
- `scripts/validate-deployment.sh` (new)

#### Commit 8: Add validation to Makefile
```bash
feat(make): Add validation targets to Makefile

- make validate (full validation)
- make validate-secrets
- make heal-permissions
- make heal-secrets
```

**Files:**
- `Makefile` (add targets)

---

### Week 3: Integration (3 commits)

#### Commit 9: Integrate validation into deploy.sh
```bash
feat(deploy): Add validation to deployment workflow

- Pre-flight checks before deployment
- Post-deployment validation
- Automatic backup on deployment
- Fail fast on validation errors
```

**Files:**
- `deploy.sh` (add validation calls)
- `scripts/setup-phase*.sh` (add validation)

#### Commit 10: Add deployment health checks
```bash
feat(health): Add comprehensive health check system

- Container health checks
- Secret health checks
- Age key health checks
- API connectivity tests
```

**Files:**
- `scripts/health-check.sh` (new)
- `src/ai_agents/deployment/health.py` (new)

#### Commit 11: Update documentation
```bash
docs(deploy): Update deployment documentation

- Document validation workflow
- Document healing commands
- Document backup procedures
- Add troubleshooting guide
```

**Files:**
- `docs/DEPLOYMENT_VALIDATION.md` (new)
- `docs/TROUBLESHOOTING.md` (new)
- `README.md` (update)

---

## Validation Workflow

### Pre-Deployment Checks:
```bash
✓ Running as root/sudo
✓ Podman installed
✓ Age installed
✓ Python 3.10+ available
✓ Required directories writable
```

### Deployment Validation:
```bash
✓ Containers running
✓ Age key exists
✓ Age key has 600 permissions
✓ Can extract public key
✓ All secrets exist
✓ All secrets have 600 permissions
✓ All secrets decrypt successfully
✓ Python package installed
```

### Healing Commands:
```bash
make heal-permissions  # Fix file permissions
make heal-secrets      # Re-encrypt corrupted secrets
make heal-containers   # Restart failed containers
make heal-all          # Fix everything
```

---

## Testing Strategy

### Unit Tests:
- Test each validation function
- Test each healing function
- Test backup encryption/decryption
- Test permission checks

### Integration Tests:
- Test full deployment workflow
- Test validation failures
- Test healing workflows
- Test backup/restore cycle

### Manual Tests:
- Fresh deployment on clean system
- Deployment with missing age key
- Deployment with corrupted secrets
- Deployment with wrong permissions

---

## Success Criteria

### Backup System:
- ✅ All backups encrypted
- ✅ Validation after every backup
- ✅ Secure storage location
- ✅ Tested restore process
- ✅ 100% test coverage

### Secrets Validation:
- ✅ Age key validated on deploy
- ✅ Secrets validated on deploy
- ✅ Permissions checked
- ✅ Healing commands work
- ✅ Clear error messages

### Deployment Reproducibility:
- ✅ Can deploy on fresh system
- ✅ Can re-deploy safely
- ✅ Can recover from failures
- ✅ Can restore from backup
- ✅ Documentation complete

---

## Timeline

| Week | Focus | Commits | Status |
|------|-------|---------|--------|
| **Week 1** | Secure Backup | 4 commits | 🟡 Starting |
| **Week 2** | Secrets Validation | 4 commits | ⚪ Planned |
| **Week 3** | Integration | 3 commits | ⚪ Planned |

**Total**: 11 commits over 3 weeks

---

## Migration from Old System

### Old Backups:
```bash
# If you have old backups in /tmp/ai-backups/
# They are NOT encrypted properly

# Recommended: Create new secure backup
make py-backup-secure

# Then delete old backups
sudo rm -rf /tmp/ai-backups/
```

### Old Deployment:
```bash
# Old deployment (no validation)
make deploy  # Just runs scripts

# New deployment (with validation)
make deploy  # Runs scripts + validation + backup
```

---

## Commands Reference

### Backup Commands:
```bash
# Secure backups (encrypted)
make py-backup-secure         # Create encrypted backup
make py-list-backups-secure   # List backups
make py-restore-secure        # Restore with safety backup

# Legacy backups (deprecated)
make py-backup               # Old unencrypted backup
make backup                  # Old tar.gz backup
```

### Validation Commands:
```bash
make validate                # Validate everything
make validate-secrets        # Validate secrets only
make validate-age-key        # Validate age key
make py-verify-secrets       # Python secret validation
```

### Healing Commands:
```bash
make heal-permissions        # Fix file permissions
make heal-secrets            # Re-encrypt secrets
make heal-containers         # Restart containers
make heal-all                # Fix everything
```

### Deployment Commands:
```bash
make deploy                  # Deploy with validation
make reconfigure             # Reconfigure with validation
make health-check            # Run health checks
```

---

## Next Steps

1. **Start with Week 1** - Secure backup implementation
2. **Test thoroughly** - Backup/restore cycles
3. **Move to Week 2** - Secrets validation
4. **Test again** - Validation workflows
5. **Week 3** - Integration and documentation

**Goal**: Rock-solid deployment before adding Cerebras! 🚀

---

## Current Status

**Phase 4.5**: ✅ Complete (8 commits - project management)
**Python Deployment**: ✅ Complete (4 modules)
**Secure Deployment**: 🟡 Starting (11 commits planned)

Let's build a bulletproof system! 🔒
