import os
import argparse
from typing import List, Dict, Any
import datetime

from langchain_huggingface import HuggingFaceEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_qdrant import Qdrant
from langchain_core.documents import Document
from qdrant_client import QdrantClient, models

from .core.config import config
from .core.exceptions import DataLoadingError, VectorStoreError
from .services.embedding_service import EmbeddingService


# --- Helper Functions ---

def load_documents_from_directory(directory: str) -> List[Document]:
    """
    Loads text content from all .txt and .md files in the specified directory
    and converts them into LangChain Document objects, including metadata
    like source filename, creation time, modification time, and ingestion timestamp.
    """
    documents = []
    if not os.path.exists(directory):
        print(f"Warning: Source directory '{directory}' does not exist. Please create it and add your documents.")
        return documents

    ingestion_timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()

    for filename in os.listdir(directory):
        filepath = os.path.join(directory, filename)
        if os.path.isfile(filepath) and (filename.endswith(".txt") or filename.endswith(".md")):
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    content = f.read()

                    # Get file stats for creation/modification times
                    file_stats = os.stat(filepath)
                    creation_time = datetime.datetime.fromtimestamp(file_stats.st_ctime, datetime.timezone.utc).isoformat()
                    modification_time = datetime.datetime.fromtimestamp(file_stats.st_mtime, datetime.timezone.utc).isoformat()

                    # Add comprehensive metadata
                    metadata = {
                        "source": filename,
                        "file_path": filepath,
                        "file_type": os.path.splitext(filename)[1],
                        "file_size_bytes": file_stats.st_size,
                        "creation_time_utc": creation_time,
                        "modification_time_utc": modification_time,
                        "ingestion_timestamp_utc": ingestion_timestamp,
                    }
                    documents.append(Document(page_content=content, metadata=metadata))
                print(f"Loaded: {filename} with metadata.")
            except Exception as e:
                print(f"Error loading {filename}: {e}")
    return documents

def split_documents(documents: List[Document]) -> List[Document]:
    """
    Splits large documents into smaller, manageable chunks.
    The metadata from the original document is preserved for each chunk.
    """
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000, 
        chunk_overlap=200,
        length_function=len,
        add_start_index=True,
    )
    chunks = text_splitter.split_documents(documents)
    print(f"Split {len(documents)} documents into {len(chunks)} chunks.")
    return chunks

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

def build_semantic_memory(
    source_directory: str = None,
    collection_name: str = None
):
    """
    Main function to build the semantic memory:
    1. Loads documents from the specified directory.
    2. Splits documents into chunks.
    3. Initializes Qdrant and uploads chunks with embeddings.
    """
    print("\n--- Starting Semantic Memory Build Process ---")
    
    # Use config defaults if not provided
    source_dir = source_directory or config.semantic_data_dir
    collection = collection_name or config.semantic_memory_collection

    # 1. Load documents
    raw_documents = load_documents_from_directory(source_dir)
    if not raw_documents:
        raise DataLoadingError(f"No documents found in '{source_dir}'. Please ensure it contains .txt or .md files.")

    # 2. Split documents into chunks
    chunks = split_documents(raw_documents)

    # 3. Initialize services
    embedding_service = initialize_embeddings()
    qdrant_client = initialize_qdrant_client()

    # Get embedding size
    embeddings_size = embedding_service.get_embedding_size()
    print(f"Determined embedding size: {embeddings_size}")

    create_or_recreate_collection(qdrant_client, collection, embeddings_size)

    try:
        qdrant_vectorstore = Qdrant(
            client=qdrant_client,
            collection_name=collection,
            embeddings=embedding_service._embeddings,
        )
        
        # Add chunks to Qdrant
        print(f"Adding {len(chunks)} chunks to Qdrant collection '{collection}'...")
        qdrant_vectorstore.add_documents(chunks)
        print("Semantic Memory built successfully in Qdrant!")
        print(f"Total points in collection '{collection}': {qdrant_client.count(collection_name=collection).count}")

    except Exception as e:
        raise VectorStoreError(f"Failed to build semantic memory: {e}")

# --- Main Execution ---
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Build semantic memory using configurable settings."
    )
    parser.add_argument(
        "--source_dir",
        type=str,
        help=f"Directory containing personal documents. Default: {config.semantic_data_dir}",
    )
    parser.add_argument(
        "--collection_name",
        type=str,
        help=f"Name of the Qdrant collection. Default: {config.semantic_memory_collection}",
    )
    
    args = parser.parse_args()

    try:
        build_semantic_memory(
            source_directory=args.source_dir,
            collection_name=args.collection_name
        )
        print("\n--- Semantic Memory Build Process Completed Successfully ---")
    except Exception as e:
        print(f"\n--- Error: {e} ---")
        exit(1)