"""
FastAPI Backend for Autonomous MirAI Student Policy Advisor
Exposes:
- POST /ingest: Accepts a PDF file via multipart/form-data, processes chunks, updates ChromaDB.
- POST /chat: Accepts a JSON payload with student question, executes strict LCEL RAG chain, returns answer.
- GET /health: Health check endpoint.
"""

import os
import shutil
import tempfile
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, UploadFile, File, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn
from dotenv import load_dotenv

# Load environment
load_dotenv()

from rag_pipeline import ingest_pdf, query_policy, get_vectorstore, COLLECTION_NAME

app = FastAPI(
    title="MirAI Student Policy Advisor API",
    description="Production-grade Strict Document RAG backend powered by LangChain and Google Gemini",
    version="1.0.0"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    question: str = Field(..., description="Student inquiry regarding university policy", min_length=1)

class DocumentMetadata(BaseModel):
    content: str
    metadata: Dict[str, Any]

class ChatResponse(BaseModel):
    status: str = "success"
    question: str
    answer: str
    expanded_queries: List[str] = []
    retrieved_documents_count: int
    retrieved_context: List[DocumentMetadata] = []

class IngestResponse(BaseModel):
    status: str
    file_name: str
    total_pages: int
    total_chunks: int
    message: str

@app.get("/")
async def root():
    return {
        "service": "Autonomous MirAI Student Policy Advisor API",
        "status": "online",
        "docs_url": "/docs",
        "health_url": "/health"
    }

@app.get("/health")
async def health():
    """Health check endpoint to verify vector store and API configuration."""
    api_key_set = bool(os.getenv("GOOGLE_API_KEY"))
    return {
        "status": "healthy" if api_key_set else "unhealthy",
        "api_key_configured": api_key_set,
        "collection_name": COLLECTION_NAME
    }

@app.post("/ingest", response_model=IngestResponse, status_code=status.HTTP_201_CREATED)
async def ingest_endpoint(file: UploadFile = File(...)):
    """
    Accepts a PDF file via multipart/form-data, processes semantic chunks,
    and updates the persistent ChromaDB vector store.
    """
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file format. Only PDF files are supported."
        )

    # Save uploaded file to a temporary file
    temp_dir = tempfile.mkdtemp()
    temp_file_path = os.path.join(temp_dir, file.filename)

    try:
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Run ingestion pipeline
        result = ingest_pdf(temp_file_path)
        return IngestResponse(**result)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to ingest document: {str(e)}"
        )
    finally:
        # Clean up temporary file
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir, ignore_errors=True)

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """
    Accepts student question, executes strict LCEL RAG chain,
    and returns deterministic, hallucination-free policy answer.
    """
    if not request.question or not request.question.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Question cannot be empty."
        )

    try:
        result = query_policy(request.question.strip())
        return ChatResponse(
            status="success",
            question=result["question"],
            answer=result["answer"],
            expanded_queries=result.get("expanded_queries", []),
            retrieved_documents_count=result["retrieved_documents_count"],
            retrieved_context=[
                DocumentMetadata(
                    content=doc["content"],
                    metadata=doc.get("metadata", {})
                ) for doc in result.get("retrieved_context", [])
            ]
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing policy query: {str(e)}"
        )

if __name__ == "__main__":
    uvicorn.run("backend:app", host="0.0.0.0", port=8000, reload=True)
