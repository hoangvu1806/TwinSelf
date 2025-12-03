# TwinSelf - Core Library

A RAG-based chatbot library that creates a digital twin using three types of memory: Semantic, Episodic, and Procedural.

## Features

- **RAG Architecture**: Retrieval-Augmented Generation with Qdrant vector database
- **Three Memory Types**: Semantic (facts), Episodic (examples), Procedural (rules)
- **Version Control**: Data versioning with snapshot and rollback support
- **Incremental Updates**: Smart rebuild only changed data
- **Vietnamese Support**: Optimized for Vietnamese language

## Installation

```bash
pip install -r requirements.txt
```

## Quick Start

### 1. Configure Environment

```bash
cp .env.example .env
# Edit .env and add your GOOGLE_API_KEY
```

### 2. Prepare Your Data

**Semantic Data** (facts) - `semantic_data/*.md`:
```markdown
# About Me
I am a software engineer...
```

**Episodic Data** (examples) - `episodic_data/*.json`:
```json
[
  {
    "user_query": "What are your skills?",
    "your_response": "I am proficient in Python..."
  }
]
```

**Procedural Data** (rules) - `procedural_data/*.json`:
```json
[
  {
    "rule": "Always respond in first person",
    "example": "I have experience in..."
  }
]
```

### 3. Build Memory

```bash
python scripts/smart_rebuild.py --create-version
```

### 4. Use in Your Code

```python
from twinself import DigitalTwinChatbot

# Initialize chatbot
chatbot = DigitalTwinChatbot()

# Chat
response = chatbot.chat("What are your skills?")
print(response)

# Chat with context
context = "Previous conversation..."
response = chatbot.chat("Tell me more", context=context)
print(response)

# Streaming
for chunk in chatbot.chat("Hello", stream=True):
    print(chunk, end="", flush=True)
```

## Library Structure

```
twinself/
├── __init__.py              # Main exports
├── chatbot.py               # DigitalTwinChatbot class
├── core/
│   ├── config.py            # Configuration
│   ├── version_manager.py   # Version control
│   ├── incremental_builder.py  # Smart rebuild
│   └── exceptions.py        # Custom exceptions
├── services/
│   └── embedding_service.py # Embedding generation
└── utils/
    ├── prompt_loader.py     # System prompt loader
    └── generate_rules_from_episodic_data.py
```

## Scripts

```bash
# Build memory from data files
python scripts/smart_rebuild.py --create-version

# Validate data files
python scripts/validate_data.py

# Manage versions
python scripts/version_manager_cli.py list
python scripts/version_manager_cli.py rollback <version_id>

# Manage system prompts
python scripts/manage_system_prompt.py list
python scripts/manage_system_prompt.py create my_prompt.md

# Process user feedback
python scripts/process_user_suggestions.py --merge --archive
```

## Configuration

Edit `.env`:

```bash
# Required
GOOGLE_API_KEY=your_api_key_here

# Optional
USER_PREFIX=your_name
EMBEDDING_MODEL_NAME=dangvantuan/vietnamese-document-embedding
MODEL_CACHE_FOLDER=./models
```

## API Reference

### DigitalTwinChatbot

```python
from twinself import DigitalTwinChatbot

chatbot = DigitalTwinChatbot(
    bot_name="YourName",           # Optional
    system_prompt="Custom prompt"  # Optional
)

# Non-streaming
response = chatbot.chat(
    user_message="Your question",
    context="Previous conversation",  # Optional
    stream=False
)

# Streaming
for chunk in chatbot.chat(user_message="Hello", stream=True):
    print(chunk, end="")

# With retrieved context
result = chatbot.chat(
    user_message="Your question",
    return_retrieved_context=True
)
print(result["response"])
print(result["retrieved_docs"])
```

## Data Management

### Version Control

```python
from twinself.core.version_manager import VersionManager

vm = VersionManager()

# List versions
versions = vm.list_versions()

# Get active version
active = vm.get_active_version()

# Rollback
vm.rollback_to_version("v1_20251201_143000")

# Create snapshot
vm.create_snapshot("v1_20251201_143000")
```

### Incremental Builder

```python
from twinself.core.incremental_builder import IncrementalBuilder

builder = IncrementalBuilder()

# Check changes
changes = builder.get_change_summary("semantic_data", "semantic")
print(f"Changes: {changes['total_changes']}")

# Update cache after rebuild
builder.update_cache("semantic_data", "semantic")
```

## Tech Stack

- **LLM**: Google Gemini
- **Embeddings**: Vietnamese Document Embedding (768 dim)
- **Vector DB**: Qdrant (local)
- **Language**: Python 3.9+

## Documentation

- [Architecture](docs/ARCHITECTURE.md)
- [Quick Start](docs/QUICKSTART.md)
- [Data Management](docs/DATA_MANAGEMENT.md)

## License

MIT License

## Author

Hoang Vu - [GitHub](https://github.com/hoangvu1806)
