import os
import argparse
import datetime
import json
import uuid
from typing import List, Dict, Any

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_qdrant import Qdrant
from langchain_core.documents import Document
from qdrant_client import QdrantClient, models

from .core.config import config
from .core.exceptions import DataLoadingError, VectorStoreError
from .services.embedding_service import EmbeddingService


# --- Helper Functions ---

def load_procedural_rules(directory: str) -> List[Dict[str, str]]:
    """
    Loads initial procedural rules from JSON files in the specified directory.
    Each JSON file should contain a list of objects like:
    [
        {"rule_name": "general_persona", "rule_content": "Be a friendly, knowledgeable, and professional AI assistant for Hoang Vu."},
        ...
    ]
    The 'rule_name' should be unique identifiers for different modular parts of your system prompt.
    These initial rules serve as the default behavior; they can be dynamically updated by an LLM optimizer later.
    """
    rules = []
    if not os.path.exists(directory):
        print(f"Warning: Source directory '{directory}' does not exist. Please create it and add your procedural rule JSON files.")
        return rules

    for filename in os.listdir(directory):
        filepath = os.path.join(directory, filename)
        if os.path.isfile(filepath) and filename.endswith(".json"):
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        for item in data:
                            if "rule_name" in item and "rule_content" in item:
                                rules.append(item)
                            else:
                                print(f"Warning: Skipping malformed item in {filename}. Expected 'rule_name' and 'rule_content' keys.")
                    else:
                        print(f"Warning: Skipping {filename}. Expected JSON file to contain a list of rules.")
                print(f"Loaded: {len(data) if isinstance(data, list) else 0} initial rules from {filename}")
            except json.JSONDecodeError as e:
                print(f"Error decoding JSON from {filename}: {e}")
            except Exception as e:
                print(f"Error loading {filename}: {e}")
    return rules

def convert_rules_to_documents(rules: List[Dict[str, str]]) -> List[Document]:
    """
    Converts procedural rules into LangChain Document objects.
    Each Document's page_content will be the 'rule_content',
    and 'rule_name' will be stored in metadata. A new UUID will be generated for the Qdrant ID.
    """
    documents = []
    ingestion_timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()

    for i, rule in enumerate(rules):
        rule_name = rule["rule_name"]
        
        # Generate a UUID for the Qdrant Point ID
        generated_id = str(uuid.uuid4())

        metadata = {
            "qdrant_point_id": generated_id, # Store the actual Qdrant ID in metadata
            "rule_name": rule_name,          # Keep the human-readable rule_name in metadata
            "ingestion_timestamp_utc": ingestion_timestamp,
            "type": "procedural_rule",
        }
        documents.append(Document(page_content=rule["rule_content"], metadata=metadata))
    
    print(f"Converted {len(rules)} initial rules into {len(documents)} LangChain Documents.")
    return documents


def initialize_embeddings() -> EmbeddingService:
    """
    Initializes the embedding service.
    """
    print(f"Initializing Embeddings with model: {config.embedding_model_name}")
    return EmbeddingService()

def initialize_qdrant_client() -> QdrantClient:
    """
    Initializes Qdrant client for local storage.
    """
    try:
        client = QdrantClient(
            path=config.qdrant_local_path,
            prefer_grpc=False
        )
        print(f"Initialized Qdrant client at path: {config.qdrant_local_path}")
        collections = client.get_collections()
        print(f"Successfully connected to Qdrant. Existing collections: {[c.name for c in collections.collections]}")
        return client
    except Exception as e:
        raise VectorStoreError(f"Failed to initialize Qdrant client: {e}")

def create_or_recreate_collection(client: QdrantClient, collection_name: str, embeddings_size: int):
    """
    Creates a new collection or re-creates it if it already exists,
    ensuring it's configured for vector storage.
    """
    if client.collection_exists(collection_name=collection_name):
        print(f"Collection '{collection_name}' already exists. Deleting and re-creating...")
        client.delete_collection(collection_name=collection_name)
    
    client.create_collection(
        collection_name=collection_name,
        vectors_config=models.VectorParams(size=embeddings_size, distance=models.Distance.COSINE),
    )
    print(f"Collection '{collection_name}' created/re-created successfully.")


def build_procedural_memory(
    source_directory: str = None,
    collection_name: str = None
):
    """
    Main function to build/initialize the procedural memory:
    1. Loads initial procedural rules from JSON files.
    2. Converts rules into LangChain Document objects.
    3. Initializes Qdrant and uploads documents with embeddings, using generated UUIDs as IDs.
    """
    print("\n--- Starting Procedural Memory Build Process ---")
    
    # Use config defaults if not provided
    source_dir = source_directory or config.procedural_data_dir
    collection = collection_name or config.procedural_memory_collection

    # 1. Load initial procedural rules
    raw_rules = load_procedural_rules(source_dir)
    if not raw_rules:
        raise DataLoadingError(f"No procedural rules found in '{source_dir}'. Exiting.")

    # 2. Convert rules to LangChain Documents
    documents = convert_rules_to_documents(raw_rules)

    # 3. Initialize services
    embedding_service = initialize_embeddings()
    qdrant_client = initialize_qdrant_client()
    
    # Get embedding size
    embeddings_size = embedding_service.get_embedding_size()
    print(f"Determined embedding size: {embeddings_size}")

    create_or_recreate_collection(qdrant_client, collection, embeddings_size)

    try:
        points = []
        for doc in documents:
            # Use the UUID generated and stored in metadata as the Qdrant Point ID
            point_id = doc.metadata["qdrant_point_id"] 
            vector = embedding_service.embed_query(doc.page_content)

            points.append(
                models.PointStruct(
                    id=point_id,
                    vector=vector,
                    payload={"page_content": doc.page_content, **doc.metadata}
                )
            )

        print(f"Upserting {len(points)} initial procedural rules to Qdrant collection '{collection}'...")
        qdrant_client.upsert(
            collection_name=collection,
            points=points,
            wait=True 
        )
        print("Procedural Memory built/initialized successfully in Qdrant!")
        print(f"Total points in collection '{collection}': {qdrant_client.count(collection_name=collection).count}")

    except Exception as e:
        raise VectorStoreError(f"Failed to build procedural memory: {e}")

# --- Main Execution ---
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Build procedural memory using configurable settings. "
                    "These rules serve as default behavior and can be dynamically updated by an LLM-based optimizer later."
    )
    parser.add_argument(
        "--source_dir",
        type=str,
        help=f"Directory containing initial procedural rule JSON files. Default: {config.procedural_data_dir}",
    )
    parser.add_argument(
        "--collection_name",
        type=str,
        help=f"Name of the Qdrant collection. Default: {config.procedural_memory_collection}",
    )
    
    args = parser.parse_args()

    try:
        build_procedural_memory(
            source_directory=args.source_dir,
            collection_name=args.collection_name
        )
        print("\n--- Procedural Memory Build Process Completed Successfully ---")
    except Exception as e:
        print(f"\n--- Error: {e} ---")
        exit(1)