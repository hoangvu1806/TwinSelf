# Quick Start

## Prerequisites

- Python 3.9+
- Google API Key (Gemini)

## Installation

```bash
# Clone repository
git clone <repo-url>
cd TwinSelf

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and add your GOOGLE_API_KEY
```

## First Run

### 1. Build Memory

```bash
# Build all memories from data files
python scripts/smart_rebuild.py --create-version
```

This will:
- Process `semantic_data/*.md` files
- Process `episodic_data/*.json` files
- Process `procedural_data/*.json` files
- Create embeddings and store in Qdrant
- Create a version snapshot

### 2. Start Server

```bash
# Production server with MLflow
python mlops_server.py

# Or simple server
python base_server.py
```

### 3. Test Chat

```bash
curl -X POST "http://localhost:8001/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test",
    "message": "What are your skills?"
  }'
```

## Adding Your Data

### Semantic Data (Facts)

Create markdown files in `semantic_data/`:

```markdown
# About Me

I am a software engineer with 5 years of experience...

## Skills
- Python
- Machine Learning
- Web Development
```

### Episodic Data (Examples)

Create JSON files in `episodic_data/`:

```json
[
  {
    "user_query": "What projects have you worked on?",
    "your_response": "I have worked on several AI projects including..."
  }
]
```

### Procedural Data (Rules)

Create JSON files in `procedural_data/`:

```json
[
  {
    "rule": "Always respond in first person",
    "example": "I have experience in..."
  }
]
```

### Rebuild After Changes

```bash
python scripts/smart_rebuild.py --create-version
```

## Common Commands

```bash
# Rebuild memory (only changed files)
python scripts/smart_rebuild.py

# Rebuild with version snapshot
python scripts/smart_rebuild.py --create-version

# Force rebuild all
python scripts/smart_rebuild.py --force

# Validate data files
python scripts/validate_data.py

# List versions
python scripts/version_manager_cli.py list

# Rollback to version
python scripts/version_manager_cli.py rollback <version_id>
```

## Troubleshooting

### Memory not updating
```bash
# Force rebuild
python scripts/smart_rebuild.py --force --create-version
```

### Server not starting
```bash
# Check environment
python -c "from twinself.core.config import config; print(config.google_api_key[:10])"
```

### Qdrant errors
```bash
# Check Qdrant data
ls data/qdrant/twinself/
```
