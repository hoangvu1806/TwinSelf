# TwinSelf: Chatbot Mô Phỏng Bản Thân Với Bộ Nhớ Ngữ Nghĩa và MLOps Pipeline

A production-ready AI chatbot framework with RAG (Retrieval-Augmented Generation), semantic memory, and complete MLOps pipeline. Create your own digital twin with monitoring, quality evaluation, and experiment tracking.

## ✨ Features

### Core Capabilities
-   **RAG Architecture**: Retrieval-Augmented Generation với 3 loại memory
-   **Semantic Memory**: Factual knowledge và information retrieval
-   **Episodic Memory**: Personal experiences và conversation examples
-   **Procedural Memory**: Behavioral rules và interaction patterns
-   **Vector Search**: Powered by Qdrant local database

### MLOps & Production
-   **MLflow Integration**: Experiment tracking và model versioning
-   **Prometheus + Grafana**: Real-time monitoring và metrics
-   **DeepEval Quality**: Automated quality evaluation với Gemini
-   **FastAPI Server**: Production-ready REST API
-   **Docker Support**: Containerized monitoring stack

### Quality & Testing
-   **Answer Relevancy**: Đánh giá độ liên quan của câu trả lời
-   **Faithfulness**: Phát hiện hallucination
-   **Token Tracking**: Monitor token usage và costs
-   **Performance Metrics**: Response time, error rate, throughput

## Setup

### 1. Clone and Install Dependencies

```bash
git clone <repository-url>
cd twinself
pip install -r requirements.txt
```

### 2. Configure Environment

Copy the example environment file and fill in your API keys:

```bash
cp .env.example .env
```

Edit `.env` with your configuration:

```env
# Required
QDRANT_API_KEY=your_qdrant_api_key
QDRANT_URL=your_qdrant_cluster_url
GOOGLE_API_KEY=your_google_api_key

# Optional - Customize for your needs
USER_PREFIX=your_username
EMBEDDING_MODEL_NAME=your_preferred_embedding_model
MODEL_CACHE_FOLDER=./models
```

### 3. Prepare Your Data

Create your data in the respective folders:

-   `semantic_data/`: Factual information (about the person, skills, education, etc.)
-   `episodic_data/`: Conversation examples and experiences (JSON format)
-   `procedural_data/`: Behavioral rules and interaction patterns

### 4. Build Your Memory System

```python
from twinself import build_semantic_memory, build_episodic_memory, build_procedural_memory

# Build all memory types
build_semantic_memory()
build_episodic_memory()
build_procedural_memory()
```

### 5. Use Your Digital Twin

```python
from twinself import DigitalTwinChatbot

# Create a digital twin with a specific name
chatbot = DigitalTwinChatbot(bot_name="Alex")
response = chatbot.chat("Tell me about yourself")
print(response)
```

## Configuration Options

### Embedding Models

Choose an embedding model that fits your language and use case:

**For English:**

```env
EMBEDDING_MODEL_NAME=sentence-transformers/all-MiniLM-L6-v2
```

**For Vietnamese:**

```env
EMBEDDING_MODEL_NAME=dangvantuan/vietnamese-document-embedding
```

**For Multilingual:**

```env
EMBEDDING_MODEL_NAME=sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
```

### User Prefix

Set a unique prefix for your collections to avoid conflicts:

```env
USER_PREFIX=john_doe  # Collections will be: john_doe_semantic_memory, etc.
```

## Data Structure

### Semantic Data

Place markdown or text files in `semantic_data/`:

-   `about.md` - Basic information about the person
-   `skills.md` - Skills and expertise
-   `education.md` - Educational background
-   `experience.md` - Work experience
-   `projects.md` - Projects and achievements

### Episodic Data

Place JSON files in `episodic_data/` with conversation examples:

```json
[
    {
        "user_query": "What's your favorite programming language?",
        "your_response": "I really enjoy Python for its simplicity and versatility. It's great for both data science and web development."
    },
    {
        "user_query": "Tell me about a challenging project you worked on",
        "your_response": "I once built a real-time chat application that had to handle thousands of concurrent users. The scaling challenges were intense but rewarding to solve."
    }
]
```

### Procedural Data

The system can automatically generate procedural rules from episodic data, or you can manually define them:

```json
[
    {
        "rule_name": "general_persona",
        "rule_content": "Be friendly, helpful, and enthusiastic. Use a conversational tone and show genuine interest in helping others."
    },
    {
        "rule_name": "technical_discussions",
        "rule_content": "When discussing technical topics, provide clear explanations with examples. Avoid jargon unless necessary."
    }
]
```

## API Requirements

-   **Qdrant Cloud**: For vector database storage
-   **Google AI**: For LLM chat capabilities

## Use Cases

-   **Personal AI Assistant**: Create a digital version of yourself
-   **Customer Service Bot**: Build persona-based customer support
-   **Educational Tutor**: Develop subject-specific teaching assistants
-   **Character AI**: Create consistent fictional characters for games/stories
-   **Brand Personality**: Build AI that represents your company's voice

## 📚 Documentation

Tất cả documentation nằm trong thư mục `docs/`:

### Quick Start
- **docs/QUICK_REFERENCE.md** - Quick reference cho toàn bộ project
- **docs/MONITORING_SIMPLE_SETUP.md** - Setup Prometheus + Grafana
- **docs/QUICKSTART_DEEPEVAL.md** - Quick start DeepEval testing

### MLOps & Monitoring
- **docs/MLOPS_PIPELINE.md** - MLOps pipeline overview
- **docs/PROMETHEUS_GRAFANA_SETUP.md** - Full monitoring integration
- **docs/MONITORING_README.md** - Complete monitoring guide

### Testing & Quality
- **docs/TEST_DEEPEVAL_README.md** - DeepEval testing guide

### Maintenance
- **docs/ROLLBACK_GUIDE.md** - Rollback procedures
- **docs/DATA_UPDATE_PIPELINE.md** - Data update pipeline

→ Xem **docs/README.md** để biết đầy đủ documentation index

---

## 🚀 Quick Start

### 1. Setup Monitoring (Optional)
```powershell
.\setup-monitoring.ps1
```
Access: http://localhost:3456 (Grafana)

### 2. Start MLOps Server
```bash
uvicorn mlops_server:app --port 8000 --reload
```
Access: http://localhost:8000/docs

### 3. Test Quality
```bash
python test_deepeval_simple.py
```

---

## 🎯 Project Structure

```
TwinSelf/
├── twinself/              # Core chatbot package
├── docs/                  # 📚 All documentation
├── scripts/               # Utility scripts
├── monitoring-templates/  # Monitoring configs
├── mlops_server.py       # Production API server
├── setup-monitoring.ps1  # Auto setup monitoring
└── test_deepeval*.py     # Quality testing
```

---

## 🔗 Quick Links

- **API Docs**: http://localhost:8000/docs
- **Grafana**: http://localhost:3000
- **Prometheus**: http://localhost:9090
- **MLflow**: http://localhost:5000

---

## 📊 Metrics Tracked

- Request rate & response time
- Token usage & costs (USD)
- Quality scores (relevancy, faithfulness)
- Error rates & system health

---

## License

MIT License - Feel free to use and customize for any purpose.
