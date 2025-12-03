"""
Build episodic memory from personal conversation examples.
Refactored to use centralized configuration and services.
"""
import os
import argparse
from typing import List, Dict
import datetime
import json

from langchain_qdrant import Qdrant
from langchain_core.documents import Document
from qdrant_client import QdrantClient, models

from .core.config import config
from .services.embedding_service import EmbeddingService
from .core.exceptions import DataLoadingError, VectorStoreError

# --- Helper Functions ---
def load_episodic_examples(directory: str) -> List[Dict[str, str]]:
    """Load episodic examples from JSON files in the specified directory."""
    examples = []
    if not os.path.exists(directory):
        raise DataLoadingError(f"Source directory '{directory}' does not exist.")

    for filename in os.listdir(directory):
        filepath = os.path.join(directory, filename)
        if os.path.isfile(filepath) and filename.endswith(".json"):
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        for item in data:
                            if "user_query" in item and "your_response" in item:
                                examples.append(item)
                            else:
                                print(f"Warning: Skipping malformed item in {filename}.")
                    else:
                        print(f"Warning: {filename} does not contain a list of examples.")
                print(f"Loaded: {len(data) if isinstance(data, list) else 0} examples from {filename}")
            except json.JSONDecodeError as e:
                raise DataLoadingError(f"Error decoding JSON from {filename}: {e}")
            except Exception as e:
                raise DataLoadingError(f"Error loading {filename}: {e}")
    
    if not examples:
        raise DataLoadingError("No valid episodic examples found in the directory.")
    
    return examples


def convert_examples_to_documents(examples: List[Dict[str, str]]) -> List[Document]:
    documents = []
    ingestion_timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()

    for i, example in enumerate(examples):
        metadata = {
            "example_id": f"episodic_example_{i}",
            "original_user_query": example["user_query"],
            "ingestion_timestamp_utc": ingestion_timestamp,
        }
        documents.append(Document(page_content=example["your_response"], metadata=metadata))

    print(f"Converted {len(examples)} examples into {len(documents)} LangChain Documents.")
    return documents


def initialize_qdrant_client() -> QdrantClient:
    """Initialize Qdrant client using configuration."""
    try:
        client = QdrantClient(
            path=config.qdrant_local_path,
            prefer_grpc=False
        )
        print(f"Initialized Qdrant client at path: {config.qdrant_local_path}")
        collections = client.get_collections()
        print(f"Connected. Existing collections: {[c.name for c in collections.collections]}")
        return client
    except Exception as e:
        raise VectorStoreError(f"Failed to initialize Qdrant client: {e}")


def create_or_recreate_collection(client: QdrantClient, collection_name: str, embeddings_size: int):
    if client.collection_exists(collection_name=collection_name):
        print(f"Collection '{collection_name}' already exists. Deleting and re-creating...")
        client.delete_collection(collection_name=collection_name)

    client.create_collection(
        collection_name=collection_name,
        vectors_config=models.VectorParams(size=embeddings_size, distance=models.Distance.COSINE),
    )
    print(f"Collection '{collection_name}' created/re-created successfully.")


def build_episodic_memory(
    source_directory: str = None,
    collection_name: str = None
):
    """
    Build episodic memory from conversation examples.
    
    Args:
        source_directory: Directory containing episodic JSON files. Uses config default if None.
        collection_name: Qdrant collection name. Uses config default if None.
    """
    print("\n--- Starting Episodic Memory Build Process ---")
    
    # Use config defaults if not provided
    source_dir = source_directory or config.episodic_data_dir
    collection = collection_name or config.episodic_memory_collection
    
    # Initialize services
    embedding_service = EmbeddingService()
    qdrant_client = initialize_qdrant_client()
    
    # Load and process data
    raw_examples = load_episodic_examples(source_dir)
    documents = convert_examples_to_documents(raw_examples)
    
    # Get embedding size and create collection
    embeddings_size = embedding_service.get_embedding_size()
    create_or_recreate_collection(qdrant_client, collection, embeddings_size)
    
    try:
        qdrant_vectorstore = Qdrant(
            client=qdrant_client,
            collection_name=collection,
            embeddings=embedding_service._embeddings,
        )
        
        # Batch insert to avoid timeout
        batch_size = config.batch_size
        print(f"Adding {len(documents)} episodic examples in batches of {batch_size}...")
        for i in range(0, len(documents), batch_size):
            batch = documents[i:i + batch_size]
            qdrant_vectorstore.add_documents(batch)
            print(f"Inserted batch {i//batch_size + 1} ({len(batch)} docs)")
        
        print("Episodic Memory built successfully in Qdrant!")
        total_points = qdrant_client.count(collection_name=collection).count
        print(f"Total points in collection '{collection}': {total_points}")
        
    except Exception as e:
        raise VectorStoreError(f"Failed to build episodic memory: {e}")


# --- Main Execution ---
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Build episodic memory from conversation examples using configurable settings."
    )
    parser.add_argument(
        "--source_dir", 
        type=str, 
        help=f"Directory containing episodic JSON files. Default: {config.episodic_data_dir}"
    )
    parser.add_argument(
        "--collection_name", 
        type=str, 
        help=f"Qdrant collection name. Default: {config.episodic_memory_collection}"
    )
    
    args = parser.parse_args()
    
    try:
        build_episodic_memory(
            source_directory=args.source_dir,
            collection_name=args.collection_name
        )
        print("\n--- Episodic Memory Build Process Completed Successfully ---")
    except Exception as e:
        print(f"\n--- Error: {e} ---")
        exit(1)
