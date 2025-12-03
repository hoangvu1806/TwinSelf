import os
from typing import List, Dict, Any, Generator

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_qdrant import Qdrant
from qdrant_client import QdrantClient

from .core.config import config
from .core.exceptions import EmbeddingError
from .services.embedding_service import EmbeddingService

# --- Chatbot Class ---
class DigitalTwinChatbot:
    def __init__(self, bot_name: str = ""):
        print("Initializing DigitalTwinChatbot...")
        self.bot_name = bot_name
        
        # Initialize services
        self.embedding_service = EmbeddingService()
        self.llm = ChatGoogleGenerativeAI(model=config.chat_llm_model, temperature=0.7)
        self.qdrant_client = QdrantClient(
            path=config.qdrant_local_path,
            prefer_grpc=False
        )
        # Initialize Vector Stores for each memory type
        self.semantic_memory_store = Qdrant(
            client=self.qdrant_client,
            collection_name=config.semantic_memory_collection,
            embeddings=self.embedding_service._embeddings,
        )
        self.episodic_memory_store = Qdrant(
            client=self.qdrant_client,
            collection_name=config.episodic_memory_collection,
            embeddings=self.embedding_service._embeddings,
        )
        self.procedural_memory_store = Qdrant(
            client=self.qdrant_client,
            collection_name=config.procedural_memory_collection,
            embeddings=self.embedding_service._embeddings,
        )
        
        self.chat_history: List[Dict[str, str]] = [] # Store chat history in RAM

        print("Chatbot initialized successfully. Ready to load memories.")
        self.procedural_rules = [] # Initialize here to prevent error before load
        self._load_procedural_rules() # Load procedural rules once at startup

    def _load_procedural_rules(self):
        """
        Loads all procedural rules from Qdrant into memory.
        These rules form the base of the System Prompt.
        """
        try:
            points, _ = self.qdrant_client.scroll(
                collection_name=config.procedural_memory_collection, 
                limit=config.top_k_procedural, 
                with_payload=True
            )
            self.procedural_rules = [point.payload['page_content'] for point in points if 'page_content' in point.payload]
            
            if not self.procedural_rules:
                print(f"Warning: Collection '{config.procedural_memory_collection}' exists but no procedural rules were loaded. Check content.")
            else:
                print(f"Loaded {len(self.procedural_rules)} procedural rules from '{config.procedural_memory_collection}'.")
        except Exception as e:
            print(f"Error loading procedural rules: {e}. Ensure collection '{config.procedural_memory_collection}' exists and is populated.")
            self.procedural_rules = [] # Fallback to empty rules if error

    def _construct_system_prompt(self, user_query: str, return_retrieved_docs: bool = False):
        # 1. Procedural Memory (Core Persona & Behavior)
        procedural_instructions = "\n".join(self.procedural_rules)
        if not procedural_instructions:
            procedural_instructions = (
                f"You are {self.bot_name}, not an AI assistant. Speak in the first person ('I'). "
                f"Be friendly, helpful, knowledgeable, enthusiastic, and professional. "
                f"Maintain a positive and engaging tone. Always strive to respond as {self.bot_name} would."
            )
            print("Warning: No procedural rules loaded from DB. Using strong default instructions for persona.")

        # Embed user query for similarity search
        try:
            query_embedding = self.embedding_service.embed_query(user_query)
        except EmbeddingError as e:
            print(f"Error embedding query: {e}")
            # Return simplified prompt if embedding fails
            return (
                f"You are {self.bot_name}. Respond in the first person ('I'). "
                f"--- Context for {self.bot_name} ---\n"
                f"***Procedural Guidelines (How I should behave):***\n{procedural_instructions}\n"
                f"I encountered an issue retrieving my memories. Please ask simpler questions for now."
            )


        # 2. Semantic Memory (Factual Knowledge)
        semantic_facts = self.semantic_memory_store.similarity_search_by_vector(query_embedding, k=config.top_k_semantic)
        semantic_context = "\n".join([doc.page_content for doc in semantic_facts])
        if semantic_context:
            semantic_context = f"\n\n***{self.bot_name}'s Knowledge Base (Relevant Facts):***\n{semantic_context}"
        else:
            semantic_context = f"\n\n***{self.bot_name}'s Knowledge Base (Relevant Facts):***\n(No specific facts retrieved for this query.)"
        
        # 3. Episodic Memory (Style and Tone Examples)
        episodic_examples_docs = self.episodic_memory_store.similarity_search_by_vector(query_embedding, k=config.top_k_episodic)
        episodic_examples_text = "\n\n".join([
            f"--- Example Interaction ---\nUser: {doc.metadata.get('original_user_query', 'N/A')}\n{self.bot_name}: {doc.page_content}"
            for doc in episodic_examples_docs
        ])
        if episodic_examples_text:
            episodic_context = f"\n\n***{self.bot_name}'s Conversation Style (Examples):***\n{episodic_examples_text}"
        else:
            episodic_context = f"\n\n***{self.bot_name}'s Conversation Style (Examples):***\n(No specific style examples retrieved for this query.)"


        # Combine all parts into the final system prompt
        system_prompt_content = (
            f"You are {self.bot_name}. You are not an AI assistant, but {self.bot_name}'s digital self. "
            f"Respond in the first person ('I', 'me', 'my').\n"
            f"Your persona, tone, and interaction style should exactly match {self.bot_name}'s unique personality.\n"
            f"Utilize all provided context to inform your answers and communication style.\n"
            f"If information is not available, state that politely in the first person, e.g.,"
            f"--- Context for {self.bot_name} ---\n"
            f"***Procedural Guidelines (How I should behave):***\n{procedural_instructions}\n"
            f"{semantic_context}\n"
            f"{episodic_context}\n"
            f"--- End Context ---"
        )
        
        if return_retrieved_docs:
            retrieved_docs = {
                "semantic": [doc.page_content for doc in semantic_facts],
                "episodic": [doc.page_content for doc in episodic_examples_docs],
                "procedural": self.procedural_rules
            }
            return system_prompt_content, retrieved_docs
        
        return system_prompt_content

    def chat(self, user_message: str, context: str = "", stream: bool = False, save_history: bool = True, return_retrieved_context: bool = False):
        """
        Processes a user message, constructs a prompt with memory,
        interacts with the LLM, and updates chat history.
        
        Args:
            user_message: The user's message
            context: Additional context (optional)
            stream: If True, returns generator for streaming. If False, returns string.
            save_history: Whether to save to chat history
            return_retrieved_context: If True, returns dict with response and retrieved_docs
            
        Returns:
            Generator[str] if stream=True
            str if stream=False and return_retrieved_context=False
            dict if stream=False and return_retrieved_context=True
        """
        try:
            # Construct dynamic system prompt
            if return_retrieved_context:
                system_prompt_content, retrieved_docs = self._construct_system_prompt(user_message, return_retrieved_docs=True)
            else:
                system_prompt_content = self._construct_system_prompt(user_message)
                retrieved_docs = None
            
            full_context = f"User's prompt: {user_message}\n\n Context: \n{context}" if context else user_message
            
            # Prepare messages for LLM
            messages = [SystemMessage(content=system_prompt_content)]
            
            # Add historical messages (excluding the system prompt)
            for msg in self.chat_history:
                if msg['role'] == 'user':
                    messages.append(HumanMessage(content=msg['content']))
                elif msg['role'] == 'assistant':
                    messages.append(AIMessage(content=msg['content']))
            
            messages.append(HumanMessage(content=full_context))

            if stream:
                # Streaming mode - return generator (cannot return context in streaming)
                if return_retrieved_context:
                    print("Warning: return_retrieved_context is ignored in streaming mode")
                return self._chat_stream(messages, user_message, save_history)
            else:
                # Normal mode - return string or dict
                ai_response_message = self.llm.invoke(messages)
                ai_response = ai_response_message.content

                if save_history:
                    self.chat_history.append({"role": "user", "content": user_message})
                    self.chat_history.append({"role": "assistant", "content": ai_response})
                    
                    if len(self.chat_history) > 10:
                        self.chat_history = self.chat_history[-10:]
                
                if return_retrieved_context:
                    return {
                        "response": ai_response,
                        "retrieved_docs": retrieved_docs
                    }
                            
                return ai_response

        except Exception as e:
            print(f"An unexpected error occurred in chat function: {e}")
            if "ResourceExhausted" in str(e):
                error_msg = "Sorry, it seems I'm busy right now. Please try again in a few minutes!"
            else:
                error_msg = "Sorry, I can't reply at the moment. There seems to be a technical problem. Please try again later."
            
            if stream:
                return self._error_generator(error_msg)
            else:
                return error_msg
    
    def _chat_stream(self, messages, user_message: str, save_history: bool):
        """Generator for streaming chat responses."""
        ai_response = ""
        try:
            for chunk in self.llm.stream(messages):
                if hasattr(chunk, "content") and chunk.content:
                    piece = chunk.content
                    ai_response += piece
                    yield piece
            
            if save_history:
                self.chat_history.append({"role": "user", "content": user_message})
                self.chat_history.append({"role": "assistant", "content": ai_response})
                
                if len(self.chat_history) > 10:
                    self.chat_history = self.chat_history[-10:]
        except Exception as e:
            yield f"\n[Streaming Error] {e}"
    
    def _error_generator(self, error_msg: str):
        """Generator that yields error message."""
        yield error_msg



# --- Main Execution Loop for Chatbot ---
if __name__ == "__main__":
    # Get user name from environment or use default
    name = os.getenv("USER_NAME", "Digital Twin")
    chatbot = DigitalTwinChatbot(bot_name=name)

    print(f"\n--- {name} Chatbot is ready! Type 'exit' to end the conversation. ---")

    while True:
        user_input = input("\n[You]: ")
        if user_input.lower() == 'exit':
            print(f"[{name}]: Goodbye! Hope to chat with you again soon.")
            break
        
        print(f"[{name}]: ")
        for chunk in chatbot.chat(user_input, stream=True):
            print(chunk, end="", flush=True)