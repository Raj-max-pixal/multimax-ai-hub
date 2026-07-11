from typing import List, AsyncGenerator
import httpx
from services.embedding_service import EmbeddingService
import os
from dotenv import load_dotenv

load_dotenv()

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")

class RAGService:
    @staticmethod
    def build_context(search_results: dict) -> str:
        context = ""
        for i, doc in enumerate(search_results.get("documents", [[]])[0]):
            context += f"Source {i+1}:\n{doc}\n\n"
        return context
    
    @staticmethod
    def build_prompt(query: str, context: str) -> str:
        return f"""You are a helpful AI assistant. Use the following context to answer the user's question.
If you don't know the answer, just say you don't know. Don't make up information.
Always cite your sources when answering.

Context:
{context}

Question: {query}

Answer:"""
    
    @staticmethod
    async def chat_with_documents(
        query: str,
        document_ids: List[str],
        model: str = "phi3:latest"
    ) -> AsyncGenerator[str, None]:
        try:
            print(f"[RAGService] chat_with_documents called with model={model}, query={query[:50]}...")
            search_results = EmbeddingService.search(query, document_ids, n_results=5)
            context = RAGService.build_context(search_results)
            prompt = RAGService.build_prompt(query, context)
            
            async with httpx.AsyncClient(timeout=None) as client:
                async with client.stream(
                    "POST",
                    f"{OLLAMA_URL}/api/chat",
                    json={
                        "model": model,
                        "messages": [{"role": "user", "content": prompt}],
                        "stream": True
                    }
                ) as response:
                    response.raise_for_status()
                    async for chunk in response.aiter_bytes():
                        yield chunk
        except Exception as e:
            print(f"RAG error: {e}")
            raise e