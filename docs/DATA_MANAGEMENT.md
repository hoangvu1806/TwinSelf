# Data Management

## Data Sources

### Semantic Data

Location: `semantic_data/`

Format: Markdown files containing facts and information.

```
semantic_data/
├── about_me.md
├── education.md
├── experience.md
├── skills.md
└── projects.md
```

Processing:
- Chunked into smaller pieces (1000 chars, 200 overlap)
- Each chunk embedded and stored in Qdrant
- Metadata includes source file and chunk index

### Episodic Data

Location: `episodic_data/`

Format: JSON files with query-response pairs.

```json
[
  {
    "user_query": "Question from user",
    "your_response": "Your response"
  }
]
```

Processing:
- Each entry embedded as a single unit
- Used for few-shot examples in prompts

### Procedural Data

Location: `procedural_data/`

Format: JSON files with rules.

```json
[
  {
    "rule": "Rule description",
    "example": "Example of rule application"
  }
]
```

Processing:
- Rules embedded and retrieved based on query
- Guides response generation style

## Version Management

### Create Version

```bash
python scripts/smart_rebuild.py --create-version
```

Creates:
- Version entry in `data/version_registry.json`
- Snapshot in `data/snapshots/<version_id>/`

### List Versions

```bash
python scripts/version_manager_cli.py list
```

Output:
```
Version: v2_20251201_143000 [ACTIVE]
  Timestamp: 2025-12-01 14:30:00
  Collections:
    - semantic_memory: 18 points
    - episodic_memory: 54 points
    - procedural_memory: 8 points
```

### Rollback

```bash
# Rollback to specific version
python scripts/version_manager_cli.py rollback v1_20251126_112413

# Rollback data only (keep current version pointer)
python scripts/version_manager_cli.py rollback v1_20251126_112413 --data-only
```

### Compare Versions

```bash
python scripts/version_manager_cli.py diff v1_20251126_112413 v2_20251201_143000
```

## Incremental Updates

The system tracks file changes using hashes stored in `data/build_cache.json`.

### Check Changes

```bash
python scripts/smart_rebuild.py --dry-run
```

Output:
```
Analyzing changes...
  Semantic Memory:  2 changes
    - Added:       1
    - Modified:    1
    - Deleted:     0
  Episodic Memory:  0 changes
  Procedural Memory: 0 changes
```

### Rebuild Changed Only

```bash
python scripts/smart_rebuild.py
```

Only rebuilds memories with detected changes.

## System Prompts

Location: `system_prompts/`

### List Prompts

```bash
python scripts/manage_system_prompt.py list
```

### Create Prompt

```bash
python scripts/manage_system_prompt.py create my_prompt.md
```

### Show Prompt

```bash
python scripts/manage_system_prompt.py show default_prompt.md
```

## User Feedback

Endpoint: `POST /api/edit-message/suggestion`

### Submit Feedback

```bash
curl -X POST "http://localhost:8001/api/edit-message/suggestion" \
  -H "Content-Type: application/json" \
  -d '{
    "original_question": "What are your skills?",
    "original_response": "I have some skills.",
    "suggested_response": "I am proficient in Python, AI/ML..."
  }'
```

Saved to: `episodic_data/user_suggestions.json`

### Process Feedback

```bash
# Preview
python scripts/process_user_suggestions.py --dry-run

# Process and merge
python scripts/process_user_suggestions.py --merge --archive

# Rebuild memory
python scripts/smart_rebuild.py --create-version
```

## Data Validation

```bash
python scripts/validate_data.py
```

Checks:
- JSON syntax
- Required fields
- File encoding
- Duplicate entries

## Cleanup

### Remove Unused Data

```bash
python scripts/cleanup_unused.py --dry-run
python scripts/cleanup_unused.py
```

### Clean Old Snapshots

```bash
python scripts/version_manager_cli.py cleanup --keep 5
```

Keeps only the 5 most recent snapshots.
