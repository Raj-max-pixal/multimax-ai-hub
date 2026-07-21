from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import List, Optional, Literal
import httpx
import os
import logging
from dotenv import load_dotenv
from services import (
    StorageService,
    DocumentService,
    EmbeddingService,
    RAGService
)
import json

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Multimax AI Hub API", version="0.3.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")

# In-memory document store for demo
documents_db = []

class ChatMessage(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str = ""

class ChatRequest(BaseModel):
    model: str = Field(..., min_length=1)
    messages: List[ChatMessage] = Field(..., min_length=1)

class DocumentChatRequest(BaseModel):
    query: str = Field(..., min_length=1)
    document_ids: List[str] = Field(..., min_length=1)
    model: Optional[str] = "phi3:latest"

@app.get("/")
async def root():
    return {"message": "Multimax AI Hub API", "version": "0.3.0"}

@app.get("/health")
async def health():
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            await client.get(f"{OLLAMA_URL}/api/tags")
        return {"status": "healthy", "ollama": "connected"}
    except Exception:
        return {"status": "healthy", "ollama": "disconnected"}

@app.get("/api/models")
async def get_models():
    try:
        logger.info(f"Fetching models from {OLLAMA_URL}")
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(f"{OLLAMA_URL}/api/tags")
            if response.status_code == 200:
                logger.info(f"Successfully fetched {len(response.json().get('models', []))} models")
                return response.json()
            logger.warning(f"Ollama returned status {response.status_code}")
            logger.error(f"Ollama returned status {response.status_code}: {response.text}")
            return {"models": [{"name": "phi3:latest"}, {"name": "llama3:latest"}, {"name": "qwen3:4b"}]}
    except Exception as e:
        logger.error(f"Error connecting to Ollama: {e}")
        return {"models": [{"name": "phi3:latest"}, {"name": "llama3:latest"}, {"name": "qwen3:4b"}]}

@app.post("/api/chat")
async def chat(request: ChatRequest):
    try:
        valid_messages = [m for m in request.messages if m.content and m.content.strip()]
        if not valid_messages:
            raise HTTPException(status_code=422, detail="At least one non-empty message is required")

        logger.info(f"Chat request received for model {request.model} with {len(valid_messages)} messages")
        
        async def generate():
            async with httpx.AsyncClient(timeout=None) as client:
                async with client.stream(
                    "POST",
                    f"{OLLAMA_URL}/api/chat",
                    json={
                        "model": request.model,
                        "messages": [{"role": m.role, "content": m.content} for m in valid_messages],
                        "stream": True
                    }
                ) as response:
                    response.raise_for_status()
                    async for chunk in response.aiter_bytes():
                        yield chunk
        
        return StreamingResponse(generate(), media_type="application/json")
    except httpx.HTTPStatusError as e:
        logger.error(f"Ollama HTTP error: {e.response.status_code} - {e.response.text}")
        raise HTTPException(status_code=e.response.status_code, detail=f"Ollama error: {e.response.text}")
    except Exception as e:
        logger.error(f"Chat error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to generate response")

# === Document APIs ===

@app.post("/api/documents/upload")
async def upload_documents(files: List[UploadFile] = File(...)):
    try:
        uploaded_docs = []
        
        for file in files:
            saved_file = await StorageService.save_file(file)
            document_id = saved_file["file_id"]
            
            # Extract text
            text = DocumentService.extract_text(
                saved_file["file_path"], 
                saved_file["file_type"]
            )
            
            if not text:
                raise HTTPException(status_code=400, detail=f"Could not extract text from {file.filename}")
            
            # Split into chunks
            chunks = DocumentService.split_text_into_chunks(text)
            
            # Add to ChromaDB
            EmbeddingService.add_chunks(document_id, chunks)
            
            # Add to in-memory db
            doc = {
                "id": document_id,
                "filename": saved_file["filename"],
                "saved_filename": saved_file["saved_filename"],
                "file_type": saved_file["file_type"],
                "file_size": saved_file["file_size"],
                "chunk_count": len(chunks),
                "status": "processed"
            }
            documents_db.append(doc)
            uploaded_docs.append(doc)
            
            logger.info(f"Document processed successfully: {file.filename}")
        
        return {"documents": uploaded_docs, "message": "Documents uploaded and processed successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Document upload error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to process documents: {str(e)}")

@app.get("/api/documents")
async def get_documents():
    return {"documents": documents_db}

@app.get("/api/documents/{document_id}")
async def get_document(document_id: str):
    doc = next((d for d in documents_db if d["id"] == document_id), None)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc

@app.delete("/api/documents/{document_id}")
async def delete_document(document_id: str):
    global documents_db
    doc = next((d for d in documents_db if d["id"] == document_id), None)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Delete from ChromaDB
    EmbeddingService.delete_document_chunks(document_id)
    
    # Delete file
    StorageService.delete_file(doc["saved_filename"])
    
    # Remove from db
    documents_db = [d for d in documents_db if d["id"] != document_id]
    
    logger.info(f"Document deleted: {doc['filename']}")
    
    return {"message": "Document deleted successfully"}

@app.post("/api/documents/chat")
async def chat_with_documents(request: DocumentChatRequest):
    try:
        logger.info(f"Document chat request for documents: {request.document_ids}")
        
        async def generate():
            async for chunk in RAGService.chat_with_documents(
                request.query,
                request.document_ids,
                request.model
            ):
                yield chunk
        
        return StreamingResponse(generate(), media_type="application/json")
    except Exception as e:
        logger.error(f"Document chat error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to chat with documents")

@app.post("/api/transcribe")
async def transcribe_audio(file: UploadFile = File(...)):
    logger.info(f"Transcription requested for: {file.filename}")
    return {
        "transcript": "This is a sample transcript. Whisper integration will be added in the backend."
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
