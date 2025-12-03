# TwinSelf Scripts

MLOps tools for managing TwinSelf memory pipeline.

## 📋 Available Scripts

### 🔨 smart_rebuild.py
**Smart incremental rebuild - only updates changed data**

```bash
# Basic usage (auto-detect changes)
python scripts/smart_rebuild.py

# Force rebuild everything
python scripts/smart_rebuild.py --force

# Create version snapshot
python scripts/smart_rebuild.py --create-version

# Dry run (preview changes)
python scripts/smart_rebuild.py --dry-run

# Skip procedural rule generation
python scripts/smart_rebuild.py --skip-procedural-gen
```

**Features:**
- Hash-based change detection
- Only rebuilds changed memories
- Auto-generates procedural rules
- Creates version snapshots

---

### 📦 version_manager_cli.py
**Manage memory versions, rollback, compare**

```bash
# List all versions
python scripts/version_manager_cli.py list

# Show active version
python scripts/version_manager_cli.py active

# Rollback to version
python scripts/version_manager_cli.py rollback v2_20241126_143022

# Compare versions
python scripts/version_manager_cli.py diff v1_20241125_120000 v2_20241126_143022
```

**Use cases:**
- Track changes over time
- Rollback after bad updates
- Compare version differences
- Audit trail

---

### ✅ validate_data.py
**Validate data files for CI/CD**

```bash
# Validate JSON structure
python scripts/validate_data.py --check-json

# Validate Markdown files
python scripts/validate_data.py --check-markdown

# Check data quality
python scripts/validate_data.py --quality-check

# Run all checks
python scripts/validate_data.py --check-json --check-markdown --quality-check
```

**Checks:**
- JSON syntax validity
- Required fields present
- Data structure correctness
- Minimum quality thresholds

---

### 📊 monitor_performance.py
**Monitor chatbot performance and health**

```bash
# Run performance tests
python scripts/monitor_performance.py

# View logs
cat data/performance_logs.jsonl | jq .
```

**Metrics:**
- Response time
- Success rate
- Memory retrieval quality
- Collection health

---

## 🚀 Quick Start

### First Time Setup

```bash
# 1. Make scripts executable
chmod +x scripts/*.py

# 2. Create initial version
python scripts/smart_rebuild.py --force --create-version

# 3. Verify
python scripts/version_manager_cli.py list
```

### Daily Workflow

```bash
# 1. Make changes to data files
nano semantic_data/projects.md

# 2. Smart rebuild
python scripts/smart_rebuild.py --create-version

# 3. Test
python scripts/monitor_performance.py

# 4. Deploy
git add . && git commit -m "Update data" && git push
```

### Rollback Workflow

```bash
# 1. List versions
python scripts/version_manager_cli.py list

# 2. Rollback
python scripts/version_manager_cli.py rollback v2_20241126_143022

# 3. Restart server
python advanced_server.py
```

---

## 📁 Generated Files

Scripts create these files:

```
data/
├── build_cache.json          # File hash cache
├── version_registry.json     # Version history
├── performance_logs.jsonl    # Performance metrics
└── qdrant/                   # Vector database
    └── twinself/
```

---

## 🔧 Configuration

Scripts use configuration from `twinself/core/config.py`:

```python
# Data directories
semantic_data_dir = "semantic_data"
episodic_data_dir = "episodic_data"
procedural_data_dir = "procedural_data"

# Collection names
semantic_memory_collection = f"{user_prefix}_semantic_memory_hg"
episodic_memory_collection = f"{user_prefix}_episodic_memory_hg"
procedural_memory_collection = f"{user_prefix}_procedural_memory_hg"
```

---

## 🐛 Troubleshooting

### Script fails with "Module not found"

```bash
# Ensure you're in project root
cd /path/to/twinself

# Run with python -m
python -m scripts.smart_rebuild
```

### Version registry corrupted

```bash
# Backup and reset
cp data/version_registry.json data/version_registry.json.bak
echo '{"versions": []}' > data/version_registry.json

# Rebuild
python scripts/smart_rebuild.py --force --create-version
```

### Cache out of sync

```bash
# Clear cache and force rebuild
rm data/build_cache.json
python scripts/smart_rebuild.py --force
```

---

## 📚 See Also

- [MLOPS_PIPELINE.md](../MLOPS_PIPELINE.md) - Complete MLOps guide
- [DATA_UPDATE_PIPELINE.md](../DATA_UPDATE_PIPELINE.md) - Data update workflow
- [README.md](../README.md) - Main project documentation
