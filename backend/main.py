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


memory_store: List[dict] = []
automation_store: List[dict] = []
agent_runs: List[dict] = []
# In-memory document store for demo
documents_db = []

class ChatMessage(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str = Field(..., min_length=1)
    images: Optional[List[str]] = None

class ChatRequest(BaseModel):
    model: str = Field(..., min_length=1)
    messages: List[ChatMessage] = Field(..., min_length=1)


class CodingAssistRequest(BaseModel):
    task: Literal["generate", "fix", "explain", "refactor", "tests", "readme", "api", "project", "review"]
    prompt: str = Field(..., min_length=1)
    code: Optional[str] = None
    language: Optional[str] = "TypeScript"
    model: Optional[str] = "qwen3:4b"

class ResearchRequest(BaseModel):
    query: str = Field(..., min_length=1)
    mode: Literal["web", "deep", "academic", "news", "fact-check", "report"] = "web"
    model: Optional[str] = "qwen3:4b"
    max_sources: int = Field(5, ge=1, le=10)

class ResearchSource(BaseModel):
    title: str
    url: str
    snippet: str = ""

class AgentRunRequest(BaseModel):
    goal: str = Field(..., min_length=1)
    agent_type: Literal["research", "browser", "shopping", "travel", "data", "report", "general"] = "general"
    model: Optional[str] = "qwen3:4b"
    max_steps: int = Field(5, ge=1, le=12)

class MemoryCreateRequest(BaseModel):
    content: str = Field(..., min_length=1)
    category: Literal["profile", "project", "preference", "task", "knowledge"] = "knowledge"
    tags: List[str] = []

class AutomationCreateRequest(BaseModel):
    name: str = Field(..., min_length=1)
    trigger: str = Field(..., min_length=1)
    actions: List[str] = Field(..., min_length=1)
    enabled: bool = True

class ImageGenerateRequest(BaseModel):
    prompt: str = Field(..., min_length=1)
    style: Literal["realistic", "illustration", "logo", "poster", "thumbnail"] = "illustration"
    size: Literal["square", "wide", "portrait"] = "square"

class VideoGenerateRequest(BaseModel):
    prompt: str = Field(..., min_length=1)
    style: Literal["shorts", "explainer", "ad", "tutorial", "story"] = "shorts"
    duration_seconds: int = Field(30, ge=5, le=180)
    model: Optional[str] = "qwen3:4b"

class VoiceChatRequest(BaseModel):
    transcript: str = Field(..., min_length=1)
    model: Optional[str] = "qwen3:4b"
class DocumentChatRequest(BaseModel):
    query: str = Field(..., min_length=1)
    document_ids: List[str] = Field(..., min_length=1)
    model: Optional[str] = "phi3:latest"


def _build_coding_prompt(request: CodingAssistRequest) -> str:
    task_prompts = {
        "generate": "Generate clean, production-ready code for the request.",
        "fix": "Find and fix bugs. Explain the root cause, then provide corrected code.",
        "explain": "Explain the code clearly, including flow, important functions, and edge cases.",
        "refactor": "Refactor for readability, maintainability, performance, and safety. Preserve behavior.",
        "tests": "Generate meaningful tests with edge cases and explain how to run them.",
        "readme": "Generate a polished README with setup, usage, scripts, env vars, and architecture notes.",
        "api": "Design and generate API endpoints, schemas, validation, errors, and examples.",
        "project": "Create a project plan and starter file structure with key code snippets.",
        "review": "Review the code for correctness, security, performance, and maintainability.",
    }
    code_block = f"\n\nExisting code:\n```{request.language or ''}\n{request.code}\n```" if request.code else ""
    return (
        "You are Multimax AI Hub Coding Assistant. Be practical, concise, and production-minded.\n\n"
        f"Task: {task_prompts.get(request.task, request.task)}\n"
        f"Language/stack: {request.language or 'Auto-detect'}\n"
        f"User request:\n{request.prompt}"
        f"{code_block}\n\n"
        "Return sections: Summary, Solution, Code, How to run/test, Next improvements."
    )

async def _ollama_complete(model: str, prompt: str, system: str = "You are a helpful assistant.") -> str:
    async with httpx.AsyncClient(timeout=180.0) as client:
        response = await client.post(
            f"{OLLAMA_URL}/api/chat",
            json={
                "model": model,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": prompt},
                ],
                "stream": False,
            },
        )
        response.raise_for_status()
        data = response.json()
        return data.get("message", {}).get("content") or data.get("response") or ""

def _extract_duckduckgo_results(html: str, max_sources: int) -> List[ResearchSource]:
    import html as html_lib
    import re
    results: List[ResearchSource] = []
    pattern = re.compile(r'<a[^>]+class="result__a"[^>]+href="([^"]+)"[^>]*>(.*?)</a>.*?<a[^>]+class="result__snippet"[^>]*>(.*?)</a>', re.S)
    for url, title, snippet in pattern.findall(html):
        clean_title = re.sub(r"<.*?>", "", title)
        clean_snippet = re.sub(r"<.*?>", "", snippet)
        results.append(ResearchSource(
            title=html_lib.unescape(clean_title).strip(),
            url=html_lib.unescape(url).strip(),
            snippet=html_lib.unescape(clean_snippet).strip(),
        ))
        if len(results) >= max_sources:
            break
    return results

async def _search_web(query: str, max_sources: int) -> List[ResearchSource]:
    try:
        async with httpx.AsyncClient(timeout=20.0, follow_redirects=True) as client:
            response = await client.get("https://duckduckgo.com/html/", params={"q": query})
            response.raise_for_status()
            results = _extract_duckduckgo_results(response.text, max_sources)
            if results:
                return results
    except Exception as e:
        logger.warning(f"Web search failed: {e}")

    return [
        ResearchSource(
            title="Search unavailable",
            url="local://search-unavailable",
            snippet="The research endpoint could not reach the web search provider. The AI summary will use the query only.",
        )
    ]

def _svg_data_url(prompt: str, style: str, size: str) -> str:
    import base64
    import html as html_lib
    dimensions = {"square": (1024, 1024), "wide": (1280, 720), "portrait": (720, 1280)}
    width, height = dimensions.get(size, (1024, 1024))
    safe_prompt = html_lib.escape(prompt[:180])
    safe_style = html_lib.escape(style)
    palette = {
        "realistic": ("#111827", "#2563eb", "#22c55e"),
        "illustration": ("#0f172a", "#8b5cf6", "#06b6d4"),
        "logo": ("#052e16", "#22c55e", "#facc15"),
        "poster": ("#1e1b4b", "#ec4899", "#f97316"),
        "thumbnail": ("#020617", "#ef4444", "#3b82f6"),
    }.get(style, ("#0f172a", "#22c55e", "#06b6d4"))
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
  <defs><linearGradient id="g" x1="0" x2="1" y1="0" y2="1"><stop stop-color="{palette[0]}"/><stop offset="0.55" stop-color="{palette[1]}"/><stop offset="1" stop-color="{palette[2]}"/></linearGradient><filter id="blur"><feGaussianBlur stdDeviation="50"/></filter></defs>
  <rect width="100%" height="100%" fill="url(#g)"/>
  <circle cx="{width * 0.25}" cy="{height * 0.28}" r="{min(width, height) * 0.22}" fill="white" opacity="0.18" filter="url(#blur)"/>
  <circle cx="{width * 0.78}" cy="{height * 0.72}" r="{min(width, height) * 0.26}" fill="black" opacity="0.22" filter="url(#blur)"/>
  <rect x="{width * 0.08}" y="{height * 0.12}" width="{width * 0.84}" height="{height * 0.76}" rx="42" fill="rgba(255,255,255,0.12)" stroke="rgba(255,255,255,0.35)"/>
  <text x="50%" y="42%" text-anchor="middle" font-family="Arial, sans-serif" font-size="{max(34, width // 24)}" font-weight="800" fill="white">Multimax Studio</text>
  <text x="50%" y="51%" text-anchor="middle" font-family="Arial, sans-serif" font-size="{max(22, width // 42)}" fill="white" opacity="0.9">{safe_style}</text>
  <foreignObject x="{width * 0.14}" y="{height * 0.58}" width="{width * 0.72}" height="{height * 0.22}"><div xmlns="http://www.w3.org/1999/xhtml" style="font-family:Arial,sans-serif;color:white;font-size:{max(20, width // 46)}px;text-align:center;line-height:1.35">{safe_prompt}</div></foreignObject>
</svg>'''
    return "data:image/svg+xml;base64," + base64.b64encode(svg.encode("utf-8")).decode("ascii")
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
        logger.info(f"Chat request received for model {request.model} with {len(request.messages)} messages")
        
        async def generate():
            async with httpx.AsyncClient(timeout=None) as client:
                async with client.stream(
                    "POST",
                    f"{OLLAMA_URL}/api/chat",
                    json={
                        "model": request.model,
                        "messages": [
                            {
                                **{"role": m.role, "content": m.content},
                                **({"images": m.images} if m.images else {}),
                            }
                            for m in request.messages
                        ],
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


@app.post("/api/coding/assist")
async def coding_assist(request: CodingAssistRequest):
    try:
        prompt = _build_coding_prompt(request)
        answer = await _ollama_complete(
            request.model or "qwen3:4b",
            prompt,
            "You are a senior software engineer inside Multimax AI Hub. Prioritize correct, maintainable, secure code.",
        )
        return {
            "task": request.task,
            "language": request.language,
            "model": request.model,
            "answer": answer,
        }
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=f"Ollama error: {e.response.text}")
    except Exception as e:
        logger.error(f"Coding assistant error: {e}")
        raise HTTPException(status_code=500, detail=f"Coding assistant failed: {e}")

@app.post("/api/research/search")
async def research_search(request: ResearchRequest):
    try:
        search_query = request.query
        if request.mode == "academic":
            search_query = f"{request.query} research paper academic"
        elif request.mode == "news":
            search_query = f"{request.query} latest news"
        elif request.mode == "fact-check":
            search_query = f"{request.query} fact check evidence"

        sources = await _search_web(search_query, request.max_sources)
        source_text = "\n".join(
            f"[{i + 1}] {source.title}\nURL: {source.url}\nSnippet: {source.snippet}"
            for i, source in enumerate(sources)
        )
        prompt = (
            f"Research mode: {request.mode}\n"
            f"Question: {request.query}\n\n"
            f"Sources:\n{source_text}\n\n"
            "Write a helpful answer with: Key answer, Evidence by source number, Uncertainties, and Next searches. "
            "If sources are unavailable, say that clearly and provide a local reasoning-only draft."
        )
        summary = await _ollama_complete(
            request.model or "qwen3:4b",
            prompt,
            "You are Multimax Research Engine. Be careful with citations and uncertainty.",
        )
        return {
            "query": request.query,
            "mode": request.mode,
            "model": request.model,
            "sources": [source.model_dump() for source in sources],
            "summary": summary,
        }
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=f"Ollama error: {e.response.text}")
    except Exception as e:
        logger.error(f"Research error: {e}")
        raise HTTPException(status_code=500, detail=f"Research failed: {e}")

@app.post("/api/agents/run")
async def run_agent(request: AgentRunRequest):
    try:
        prompt = (
            f"Agent type: {request.agent_type}\n"
            f"Goal: {request.goal}\n"
            f"Max steps: {request.max_steps}\n\n"
            "Create an executable agent plan. Return: Objective, Assumptions, Step-by-step plan, Tools/data needed, Risks, Final deliverable. "
            "If browser/live action is needed, say what the user must approve before execution."
        )
        result = await _ollama_complete(
            request.model or "qwen3:4b",
            prompt,
            "You are Multimax Agent Planner. Plan multi-step tasks safely and concretely.",
        )
        run = {
            "id": str(len(agent_runs) + 1),
            "goal": request.goal,
            "agent_type": request.agent_type,
            "model": request.model,
            "status": "planned",
            "steps": result,
        }
        agent_runs.insert(0, run)
        return run
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=f"Ollama error: {e.response.text}")
    except Exception as e:
        logger.error(f"Agent run error: {e}")
        raise HTTPException(status_code=500, detail=f"Agent run failed: {e}")

@app.get("/api/agents/runs")
async def list_agent_runs():
    return {"runs": agent_runs}

@app.post("/api/memory")
async def create_memory(request: MemoryCreateRequest):
    item = {
        "id": str(len(memory_store) + 1),
        "content": request.content,
        "category": request.category,
        "tags": request.tags,
    }
    memory_store.insert(0, item)
    return item

@app.get("/api/memory")
async def list_memory(q: Optional[str] = None, category: Optional[str] = None):
    results = memory_store
    if category:
        results = [item for item in results if item["category"] == category]
    if q:
        query = q.lower()
        results = [item for item in results if query in item["content"].lower() or any(query in tag.lower() for tag in item["tags"])]
    return {"memories": results}

@app.delete("/api/memory/{memory_id}")
async def delete_memory(memory_id: str):
    global memory_store
    before = len(memory_store)
    memory_store = [item for item in memory_store if item["id"] != memory_id]
    if len(memory_store) == before:
        raise HTTPException(status_code=404, detail="Memory not found")
    return {"message": "Memory deleted"}

@app.post("/api/automation/workflows")
async def create_workflow(request: AutomationCreateRequest):
    workflow = {
        "id": str(len(automation_store) + 1),
        "name": request.name,
        "trigger": request.trigger,
        "actions": request.actions,
        "enabled": request.enabled,
    }
    automation_store.insert(0, workflow)
    return workflow

@app.get("/api/automation/workflows")
async def list_workflows():
    return {"workflows": automation_store}

@app.post("/api/automation/generate")
async def generate_workflow(request: ResearchRequest):
    try:
        prompt = (
            f"Automation request: {request.query}\n\n"
            "Design a workflow with: name, trigger, actions, required integrations, safety checks, and test plan. "
            "Prefer free/open-source/local tools."
        )
        summary = await _ollama_complete(
            request.model or "qwen3:4b",
            prompt,
            "You are Multimax Automation Architect. Design safe practical workflows.",
        )
        return {"summary": summary}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Workflow generation failed: {e}")

@app.post("/api/voice/chat")
async def voice_chat(request: VoiceChatRequest):
    try:
        answer = await _ollama_complete(
            request.model or "qwen3:4b",
            request.transcript,
            "You are Multimax Voice Assistant. Reply naturally and concisely for spoken playback.",
        )
        return {"transcript": request.transcript, "answer": answer, "voice": "browser-speech-synthesis"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Voice chat failed: {e}")

@app.post("/api/images/generate")
async def generate_image(request: ImageGenerateRequest):
    image_url = _svg_data_url(request.prompt, request.style, request.size)
    return {"prompt": request.prompt, "style": request.style, "size": request.size, "image_url": image_url, "note": "Local SVG image generated. Connect ComfyUI/Stable Diffusion later for photoreal generation."}

@app.post("/api/video/generate")
async def generate_video(request: VideoGenerateRequest):
    try:
        prompt = (
            f"Create a video production plan.\nPrompt: {request.prompt}\n"
            f"Style: {request.style}\nDuration: {request.duration_seconds} seconds\n\n"
            "Return: title, hook, scene-by-scene storyboard with timestamps, narration, visual prompts, subtitles, music/SFX, and export checklist."
        )
        plan = await _ollama_complete(
            request.model or "qwen3:4b",
            prompt,
            "You are Multimax Video Studio. Create practical video storyboards and generation prompts.",
        )
        frames = [_svg_data_url(f"{request.prompt} — scene {i + 1}", "thumbnail", "wide") for i in range(min(4, max(1, request.duration_seconds // 15)))]
        return {"prompt": request.prompt, "style": request.style, "duration_seconds": request.duration_seconds, "plan": plan, "frames": frames}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Video generation failed: {e}")
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
