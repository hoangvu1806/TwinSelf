# TwinSelf - Digital Twin Chatbot

A RAG-based chatbot system that creates a digital twin using three types of memory: Semantic, Episodic, and Procedural.

## Features

- **RAG Architecture**: Retrieval-Augmented Generation with Qdrant vector database
- **Three Memory Types**: Semantic (facts), Episodic (examples), Procedural (rules)
- **MLOps Pipeline**: MLflow tracking and DeepEval quality evaluation
- **Version Control**: Data versioning with snapshot and rollback support
- **User Feedback**: Collect and integrate user suggestions
- **Production Ready**: FastAPI server with streaming support

## Quick Start

### Prerequisites

- Python 3.9+
- Google API Key (Gemini)

### Installation

```bash
# Clone repository
git clone https://github.com/hoangvu1806/TwinSelf.git
cd TwinSelf

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and add your GOOGLE_API_KEY
```

### Build Memory

```bash
python scripts/smart_rebuild.py --create-version
```

### Start Server

```bash
python mlops_server.py
```

Server runs at: http://localhost:8001

API docs: http://localhost:8001/docs

## Usage

### Chat API

```bash
curl -X POST "http://localhost:8001/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "user123",
    "message": "What are your skills?"
  }'
```

### Python Client

```python
import requests

response = requests.post(
    "http://localhost:8001/chat",
    json={
        "session_id": "user123",
        "message": "Tell me about your experience"
    }
)

print(response.json()["response"])
```

## Project Structure

```
TwinSelf/
├── mlops_server.py          # Production server
├── twinself/                # Core library
│   ├── chatbot.py           # Main chatbot class
│   ├── core/                # Core components
│   └── services/            # Services (embedding, etc.)
├── scripts/                 # Utility scripts
├── semantic_data/           # Facts and knowledge (markdown)
├── episodic_data/           # Conversation examples (json)
├── procedural_data/         # Response rules (json)
├── system_prompts/          # System prompts
├── docs/                    # Documentation
└── tests/                   # Tests
```

## Adding Your Data

### Semantic Memory (Facts)

Create markdown files in `semantic_data/`:

```markdown
# About Me
I am a software engineer with 5 years of experience...
```

### Episodic Memory (Examples)

Create JSON files in `episodic_data/`:

```json
[
  {
    "user_query": "What projects have you worked on?",
    "your_response": "I have worked on several AI projects..."
  }
]
```

### Rebuild After Changes

```bash
python scripts/smart_rebuild.py --create-version
```

## Documentation

- [Architecture](docs/ARCHITECTURE.md) - System design
- [Quick Start](docs/QUICKSTART.md) - Detailed setup guide
- [API Reference](docs/API_REFERENCE.md) - API endpoints
- [Data Management](docs/DATA_MANAGEMENT.md) - Managing memory data
- [MLOps Pipeline](docs/MLOPS_PIPELINE.md) - MLflow and DeepEval
- [Deployment](docs/DEPLOYMENT.md) - Production deployment

## Key Commands

```bash
# Rebuild memory
python scripts/smart_rebuild.py --create-version

# Validate data
python scripts/validate_data.py

# List versions
python scripts/version_manager_cli.py list

# Rollback to version
python scripts/version_manager_cli.py rollback <version_id>

# Run tests
python tests/test_api.py
```

## MLOps Features

### MLflow Tracking

```bash
# Start MLflow UI
mlflow ui --host 0.0.0.0 --port 5000
```

View metrics at: http://localhost:5000

### DeepEval Quality Evaluation

Automatically evaluates response quality:
- Answer Relevancy
- Faithfulness to context

Metrics logged to MLflow asynchronously.

## Configuration

Edit `.env` file:

```bash
# Required
GOOGLE_API_KEY=your_api_key_here
GOOGLE_API_KEY_4DEEPEVAL=your_deepeval_key_here

# Optional
USER_PREFIX=your_name
EMBEDDING_MODEL_NAME=dangvantuan/vietnamese-document-embedding
```

## Tech Stack

- **LLM**: Google Gemini
- **Embeddings**: Vietnamese Document Embedding
- **Vector DB**: Qdrant (local)
- **Framework**: FastAPI
- **MLOps**: MLflow, DeepEval
- **Language**: Python 3.9+

## License

MIT License

## Author

Hoang Vu - [GitHub](https://github.com/hoangvu1806)
