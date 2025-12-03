# Architecture

## System Overview

```
User Query
    |
    v
+-------------------+
|   FastAPI Server  |
|   (mlops_server)  |
+-------------------+
    |
    v
+-------------------+
|  DigitalTwinBot   |
|    (chatbot.py)   |
+-------------------+
    |
    +---> Embedding Service (Vietnamese embeddings)
    |
    +---> Qdrant Vector DB
    |         |
    |         +---> Semantic Memory (facts, skills)
    |         +---> Episodic Memory (examples)
    |         +---> Procedural Memory (rules)
    |
    +---> Gemini LLM (response generation)
    |
    v
Response + MLflow Metrics
```

## Core Components

### 1. Chatbot (twinself/chatbot.py)

Main class that orchestrates the conversation flow:
- Retrieves relevant context from all three memory types
- Builds prompt with retrieved context
- Generates response using Gemini
- Supports streaming and non-streaming modes

### 2. Memory Types

**Semantic Memory**
- Source: `semantic_data/*.md`
- Content: Facts, skills, education, experience
- Use: Answering factual questions

**Episodic Memory**
- Source: `episodic_data/*.json`
- Content: Personal stories, conversation examples
- Use: Providing examples, maintaining personality

**Procedural Memory**
- Source: `procedural_data/*.json`
- Content: Rules for response generation
- Use: Guiding response style and format

### 3. Embedding Service (twinself/services/embedding_service.py)

- Model: `dangvantuan/vietnamese-document-embedding`
- Dimension: 768
- Cached locally in `models/` folder

### 4. Vector Database (Qdrant)

- Local storage: `data/qdrant/twinself/`
- Collections:
  - `{user}_semantic_memory_hg`
  - `{user}_episodic_memory_hg`
  - `{user}_procedural_memory_hg`

### 5. Version Manager (twinself/core/version_manager.py)

- Tracks data versions
- Creates snapshots
- Supports rollback
- Registry: `data/version_registry.json`

## Data Flow

### 1. Data Ingestion

```
Markdown/JSON files
    |
    v
Chunking (semantic) / Parsing (episodic/procedural)
    |
    v
Embedding generation
    |
    v
Qdrant vector storage
```

### 2. Query Processing

```
User query
    |
    v
Query embedding
    |
    v
Vector search (top-k from each memory)
    |
    v
Context assembly
    |
    v
Prompt construction
    |
    v
LLM generation
    |
    v
Response
```

## Configuration

All configuration in `twinself/core/config.py`:

| Setting | Default | Description |
|---------|---------|-------------|
| CHAT_LLM_MODEL | gemini-2.5-flash-lite | LLM model |
| EMBEDDING_MODEL_NAME | vietnamese-document-embedding | Embedding model |
| TOP_K_SEMANTIC | 7 | Semantic results |
| TOP_K_EPISODIC | 5 | Episodic results |
| TOP_K_PROCEDURAL | 10 | Procedural results |
| CHUNK_SIZE | 1000 | Text chunk size |
| CHUNK_OVERLAP | 200 | Chunk overlap |

## Servers

### mlops_server.py (Production)
- MLflow tracking
- DeepEval quality evaluation
- Token/cost tracking
- User feedback endpoint

### base_server.py (Simple)
- Basic chat endpoint
- No tracking
- For development/testing

### portforlio_chatbot_server.py (Portfolio)
- Stateless design
- Frontend provides history
- For portfolio website
