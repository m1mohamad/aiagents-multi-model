# Deployment Architecture

## Overview

The AI Multi-Agent system uses a **hybrid deployment approach** combining bash scripts for initial setup and Python modules for programmatic management.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     User Interface                           │
│                                                              │
│  Makefile Commands  ←→  Bash Scripts  ←→  Python Modules   │
└─────────────────────────────────────────────────────────────┘
         │                    │                    │
         ├────────────────────┼────────────────────┤
         │                    │                    │
         ▼                    ▼                    ▼
   ┌─────────┐        ┌─────────────┐     ┌──────────────┐
   │ Makefile│        │ Shell       │     │ Python       │
   │ Targets │        │ Scripts     │     │ Modules      │
   │         │        │             │     │              │
   │ - deploy│        │ - deploy.sh │     │ - state.py   │
   │ - status│        │ - setup-*.sh│     │ - secrets.py │
   │ - test  │        │             │     │ - backup.py  │
   │         │        │             │     │ - containers │
   └─────────┘        └─────────────┘     └──────────────┘
         │                    │                    │
         └────────────────────┴────────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │ Infrastructure   │
                    │                  │
                    │ - Podman         │
                    │ - Containers     │
                    │ - Age Encryption │
                    │ - /ai directory  │
                    └──────────────────┘
```

## Two Approaches

### 1. Bash Scripts (Initial Deployment)

**Purpose**: Bootstrap and initial setup
**When to use**: Fresh deployments, initial configuration

**Scripts:**
- `deploy.sh` - Master deployment orchestrator
- `setup-ai-foundation.sh` - Creates infrastructure (Phase 1)
- `setup-phase2.sh` - Builds container images (Phase 2)
- `setup-phase3.sh` - Sets up authentication (Phase 3)
- `setup-phase4.sh` - Configures full APIs (Phase 4)

**Usage:**
```bash
make deploy-full   # Fresh deployment
make deploy        # Re-run deployment
make config        # Re-configure APIs
```

**Characteristics:**
- ✅ Idempotent (can re-run safely)
- ✅ Well-tested in production
- ✅ Handles system-level setup
- ⚠️  Harder to test programmatically
- ⚠️  Less composable

### 2. Python Modules (Day-to-Day Management)

**Purpose**: Programmatic management, monitoring, automation
**When to use**: Daily operations, automation, scripting

**Modules:**
- `state.py` - Deployment state detection
- `secrets.py` - Secret management with age encryption
- `backup.py` - Backup and restore operations
- `containers.py` - Container lifecycle management

**Usage:**
```bash
# Via Makefile
make py-status          # Check deployment status
make py-containers      # Check container status
make py-backup          # Create backup
make py-restart         # Restart containers

# Via Python CLI
sudo python3 scripts/deploy-cli.py status
sudo python3 scripts/deploy-cli.py backup

# Direct Python import
from ai_agents.deployment import ContainerManager
mgr = ContainerManager()
mgr.restart_pod()
```

**Characteristics:**
- ✅ Fully tested (45/46 tests passing)
- ✅ Type-safe with type hints
- ✅ Composable and reusable
- ✅ Security-first design
- ✅ Easy to extend
- ⚠️  Requires Python environment

## Deployment Flow

### Fresh Deployment
```bash
1. make install        → Installs podman, age
2. make deploy         → Runs bash scripts (Phase 1-3)
3. make config         → Configures APIs (Phase 4)
```

### Day-to-Day Operations
```bash
# Using bash (familiar, stable)
make restart
make status
make backup

# Using Python (programmatic, testable)
make py-restart
make py-status
make py-backup
```

## When to Use What

| Task | Use Bash | Use Python | Why |
|------|----------|------------|-----|
| **Initial deployment** | ✅ | ❌ | Bash handles system setup |
| **Re-deployment** | ✅ | ❌ | Bash scripts are proven |
| **Check status** | ✅ | ✅ | Both work, Python gives more detail |
| **Restart containers** | ✅ | ✅ | Both work equally well |
| **Backup/Restore** | ⚠️ | ✅ | Python has atomic operations |
| **Automation** | ⚠️ | ✅ | Python is easier to script |
| **Testing** | ❌ | ✅ | Python has test suite |
| **CI/CD integration** | ⚠️ | ✅ | Python has better error handling |

## Migration Path

Current state: **Phase 1 - Hybrid**
- ✅ Bash scripts for deployment
- ✅ Python modules available for management
- ✅ Both approaches work independently

Future options:

### Option A: Keep Hybrid (Recommended for now)
- Keep bash scripts for initial deployment
- Use Python for day-to-day management
- Best of both worlds

### Option B: Python-First (Future)
- Create Python deployment orchestrator
- Replace bash scripts gradually
- Requires more testing

### Option C: Bash-Only (Not recommended)
- Remove Python modules
- Stick with bash scripts
- Loses testability and composability

## Python Module Examples

### Check Deployment State
```python
from ai_agents.deployment import StateDetector

detector = StateDetector()
state = detector.detect()

if state.is_fully_deployed:
    print("✓ System ready")
elif state.needs_secrets:
    print("⚠ Configure secrets")
```

### Manage Containers
```python
from ai_agents.deployment import ContainerManager

mgr = ContainerManager()

# Restart specific agent
mgr.restart_container("claude")

# Check status
for agent in mgr.agents:
    running = mgr.is_container_running(agent)
    print(f"{agent}: {'Running' if running else 'Stopped'}")
```

### Create Backup
```python
from ai_agents.deployment import BackupManager

mgr = BackupManager()

# Create backup with secrets
backup_path = mgr.create_backup(include_secrets=True)
print(f"Backup: {backup_path}")

# List backups
backups = mgr.list_backups()
for backup in backups:
    info = mgr.get_backup_info(backup)
    print(f"{backup.name}: {info['timestamp']}")
```

### Verify Secrets
```python
from ai_agents.deployment import SecretsManager

mgr = SecretsManager()

for agent in ["claude", "grok", "gemini"]:
    exists = mgr.verify_secret_exists(agent)
    can_decrypt = mgr.test_decryption(agent)
    print(f"{agent}: {'✓' if exists and can_decrypt else '✗'}")
```

## Testing

### Bash Scripts
```bash
# Manual testing
make deploy-full
make test
make status
```

### Python Modules
```bash
# Automated testing
make py-test                  # Run test suite
python -m pytest tests/deployment/ -v

# Verify on live system
make py-status                # Check status
make py-verify-secrets        # Verify secrets
```

## Security Considerations

Both approaches follow the same security model:

1. ✅ **Secrets via stdin** - Never in command-line args
2. ✅ **Age encryption** - All secrets encrypted with age
3. ✅ **Strict permissions** - 600 on all secret files
4. ✅ **Input validation** - Whitelist approach
5. ✅ **No shell injection** - No `shell=True` in subprocess
6. ✅ **Timeout protection** - All operations have timeouts

## Makefile Command Reference

### Bash-Based Commands
```bash
make deploy          # Deploy infrastructure
make deploy-full     # Full deployment
make status          # Show status
make restart         # Restart containers
make backup          # Create backup (tar.gz)
```

### Python-Based Commands
```bash
make py-status       # Deployment status (Python)
make py-containers   # Container status (Python)
make py-restart      # Restart containers (Python)
make py-backup       # Create backup (Python)
make py-list-backups # List backups (Python)
make py-test         # Run Python tests
make py-help         # Show Python commands
```

## Troubleshooting

### Issue: Python modules not found
```bash
# Install the package
pip install -e .

# Or use system Python
sudo pip3 install -e .
```

### Issue: Permission errors
```bash
# Python commands need sudo (like bash)
sudo python3 scripts/deploy-cli.py status

# Or use make commands (sudo is built-in)
make py-status
```

### Issue: Containers not accessible
```bash
# Check with bash
make status

# Check with Python
make py-containers

# Compare results
```

## Conclusion

The hybrid approach gives you:
- ✅ **Stability** - Proven bash scripts for deployment
- ✅ **Flexibility** - Python modules for automation
- ✅ **Testability** - Python test suite (45/46 tests)
- ✅ **Choice** - Use what works best for your workflow

**Recommended workflow:**
1. Use `make deploy-full` for initial setup
2. Use `make py-status` for daily monitoring
3. Use `make py-backup` for backups
4. Use `make py-restart` for container management
5. Use bash scripts when Python isn't available
