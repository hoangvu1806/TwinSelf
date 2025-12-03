# TwinSelf Documentation

## Overview

TwinSelf is a Digital Twin chatbot system that uses RAG (Retrieval-Augmented Generation) with three types of memory:
- Semantic Memory: Facts, skills, education, experience
- Episodic Memory: Personal stories, examples, conversations
- Procedural Memory: Rules for how to respond

## Documentation Index

1. [Architecture](ARCHITECTURE.md) - System design and components
2. [Quick Start](QUICKSTART.md) - Get started in 5 minutes
3. [Data Management](DATA_MANAGEMENT.md) - Managing memory data
4. [API Reference](API_REFERENCE.md) - Server endpoints
5. [MLOps Pipeline](MLOPS_PIPELINE.md) - MLflow, DeepEval integration
6. [Deployment](DEPLOYMENT.md) - Production deployment guide

## Quick Commands

```bash
# Start server
python mlops_server.py

# Rebuild memory
python scripts/smart_rebuild.py --create-version

# Run tests
python -m pytest tests/

# Check data
python scripts/validate_data.py
```

## Project Structure

```
TwinSelf/
├── mlops_server.py          # Main production server
├── twinself/                # Core library
│   ├── chatbot.py           # Main chatbot class
│   ├── core/                # Core components
│   └── services/            # Services (embedding, etc.)
├── scripts/                 # Utility scripts
├── data/                    # Qdrant database
├── semantic_data/           # Semantic memory (markdown)
├── episodic_data/           # Episodic memory (json)
├── procedural_data/         # Procedural rules (json)
└── system_prompts/          # System prompts
```
