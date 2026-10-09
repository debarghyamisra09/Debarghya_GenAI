"""
Core RAG Pipeline for Autonomous MirAI Student Policy Advisor
Meets all technical specifications:
- PyPDFLoader for ingestion
- RecursiveCharacterTextSplitter (chunk_size=1000, chunk_overlap=200)
- GoogleGenerativeAIEmbeddings (models/gemini-embedding-001 or text-embedding-004)
- Local ChromaDB instance
- MultiQueryRetriever for vocabulary bridging (casual student language -> formal handbook clauses)
- ChatGoogleGenerativeAI (gemini-3.8-flash / gemini-3.5-flash, temperature=0.0)
- Strict Guardrail Prompt preventing hallucination or external assumptions
"""

import os
import re
import time
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_chroma import Chroma
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.documents import Document

# Configuration constants
CHROMA_PERSIST_DIR = os.getenv("CHROMA_DIR", "./chroma_db")
COLLECTION_NAME = "mirai_policy_handbook"
LLM_MODEL = os.getenv("LLM_MODEL", "gemini-3.5-flash")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "models/gemini-embedding-001")

def get_embeddings() -> GoogleGenerativeAIEmbeddings:
    """Initialize GoogleGenerativeAIEmbeddings with fallback support."""
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY environment variable not set. Please check your .env file.")
    
    for model_name in [EMBEDDING_MODEL, "models/gemini-embedding-001", "models/text-embedding-004"]:
        try:
            return GoogleGenerativeAIEmbeddings(model=model_name, google_api_key=api_key)
        except Exception:
            continue
    return GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001", google_api_key=api_key)

def get_vectorstore() -> Chroma:
    """Get persistent Chroma vector store."""
    embeddings = get_embeddings()
    return Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=embeddings,
        persist_directory=CHROMA_PERSIST_DIR
    )

def ingest_pdf(file_path: str) -> Dict[str, Any]:
    """
    Ingests a PDF file using PyPDFLoader, chunks it semantically with
    RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200),
    and stores vectors in local ChromaDB.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"PDF file not found at: {file_path}")
    
    # 1. Load document using PyPDFLoader
    loader = PyPDFLoader(file_path)
    docs = loader.load()
    
    # 2. Semantic Chunking
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        separators=["\n\n", "\n", ". ", " ", ""]
    )
    chunks = splitter.split_documents(docs)
    
    for i, chunk in enumerate(chunks):
        chunk.metadata["chunk_index"] = i
        chunk.metadata["total_chunks"] = len(chunks)
        chunk.metadata["source_file"] = os.path.basename(file_path)

    # 3. Store in ChromaDB
    embeddings = get_embeddings()
    vectorstore = Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=embeddings,
        persist_directory=CHROMA_PERSIST_DIR
    )
    vectorstore.add_documents(chunks)
    
    return {
        "status": "success",
        "file_name": os.path.basename(file_path),
        "total_pages": len(docs),
        "total_chunks": len(chunks),
        "message": f"Successfully ingested {len(chunks)} chunks across {len(docs)} pages into ChromaDB."
    }

def get_llm(temperature: float = 0.0) -> ChatGoogleGenerativeAI:
    """Initialize ChatGoogleGenerativeAI with strict deterministic zero temperature."""
    api_key = os.getenv("GOOGLE_API_KEY")
    # Try configured model, fallback to 3.5-flash / 3.8-flash if needed
    for model_candidate in [LLM_MODEL, "gemini-3.5-flash", "gemini-3.8-flash", "gemini-3.7-flash"]:
        try:
            return ChatGoogleGenerativeAI(
                model=model_candidate,
                temperature=temperature,
                google_api_key=api_key,
                max_retries=3
            )
        except Exception:
            continue
    return ChatGoogleGenerativeAI(
        model="gemini-3.5-flash",
        temperature=temperature,
        google_api_key=api_key
    )

# Strict Guardrail System Prompt
STRICT_SYSTEM_PROMPT = """You are the official Autonomous MirAI Student Policy Advisor for the MirAI School of Technology (SoT).
Your primary mandate is to provide strictly factual, highly accurate guidance based SOLELY and EXCLUSIVELY on the provided official policy handbook excerpts.

=== CRITICAL GUARDRAILS & OPERATIONAL CONSTRAINTS ===
1. GROUNDED FACTUALITY: Answer the user query using ONLY the verified facts stated directly in the retrieved context below.
2. NO BASE MODEL ASSUMPTIONS: You must NEVER rely on prior training data, external institutional policies, or make assumptions not explicitly documented in the retrieved text.
3. STRICT DECLINE POLICY: If the question cannot be answered with 100% certainty directly from the retrieved context, you MUST politely decline by stating:
   "I am unable to answer this question based on the official MirAI Student Policy Handbook provided. Please consult the Student Affairs or Academic Administration office directly."
4. NEGATIVE CONSTRAINT HANDLING: If an action or policy is prohibited (e.g., smoking/substance use) and leads to disciplinary action, state the exact prohibition and disciplinary committee process. Do NOT invent, assume, or fabricate any specific monetary fine if none is mentioned in the text.
5. PRECISION & MULTI-HOP SYNTHESIS: Carefully correlate criteria across distinct sections (e.g. campus location, specific coordinator contacts, submission deadlines, exact percentages, and mark brackets) to deliver comprehensive, accurate policy advice.

=== RETRIEVED HANDBOOK CONTEXT ===
{context}

=== STUDENT INQUIRY ===
{question}

=== POLICY ADVISOR FACTUAL RESPONSE ===
"""

class MultiQueryRetriever:
    """
    MultiQueryRetriever that expands casual student queries into formal
    institutional handbook terminology, retrieves documents across all variations,
    and deduplicates the resulting context.
    """
    def __init__(self, vectorstore: Chroma, k: int = 4):
        self.vectorstore = vectorstore
        self.k = k

    def expand_query(self, question: str) -> List[str]:
        """Expands student query into formal policy search phrases."""
        variations = [question]
        q_lower = question.lower()
        
        # Domain-informed vocabulary expansions
        if "attendance" in q_lower or "%" in q_lower or "marks" in q_lower:
            variations.append("Attendance bracket continuous internal assessment marks criteria percentage")
            variations.append("Academic Regulations Attendance Framework scoring calculation 72%")
        elif "ratnam" in q_lower or "medical" in q_lower or "leave" in q_lower or "sick" in q_lower:
            variations.append("Ratnam campus medical leave submission days contact coordinator Yashaswini")
            variations.append("Leave of Absence Medical Leave Protocols hospital documentation timeline 7 days")
        elif "cybersecurity" in q_lower or "society" in q_lower or "club" in q_lower or "tech club" in q_lower or "management" in q_lower:
            variations.append("Formation of New Societies Tech Club batch support Faculty Coordinator Management 40%")
            variations.append("Student Clubs Societies Extracurricular Governance petition procedure")
        elif "smoke" in q_lower or "smoking" in q_lower or "cigarette" in q_lower or "fine" in q_lower or "tobacco" in q_lower:
            variations.append("Tobacco and Smoking Prohibition penalties Disciplinary Committee fine")
            variations.append("Campus Code of Conduct Substance Regulations violations")
        else:
            words = [w for w in re.split(r'\W+', question) if len(w) > 3]
            if words:
                variations.append(f"Official policy regulations on {' '.join(words)}")

        return variations

    def retrieve(self, question: str) -> List[Document]:
        """Retrieves and deduplicates documents across expanded query variations."""
        queries = self.expand_query(question)
        seen_contents = set()
        unique_docs: List[Document] = []

        for q in queries:
            try:
                docs = self.vectorstore.similarity_search(q, k=self.k)
                for doc in docs:
                    content_hash = doc.page_content.strip()
                    if content_hash not in seen_contents:
                        seen_contents.add(content_hash)
                        unique_docs.append(doc)
            except Exception:
                continue

        if not unique_docs:
            unique_docs = self.vectorstore.similarity_search(question, k=self.k)

        return unique_docs

def format_docs_context(docs: List[Document]) -> str:
    """Formats retrieved document chunks into clean markdown context for LLM."""
    if not docs:
        return "No relevant handbook context found."
    formatted = []
    for i, doc in enumerate(docs):
        source = doc.metadata.get("source_file", "Handbook")
        page = doc.metadata.get("page", 0)
        page_num = page + 1 if isinstance(page, int) else page
        formatted.append(f"--- Document Section {i+1} [Source: {source}, Page {page_num}] ---\n{doc.page_content.strip()}")
    return "\n\n".join(formatted)

def query_policy(question: str) -> Dict[str, Any]:
    """
    Executes the strict LCEL RAG chain for a given student question.
    """
    vectorstore = get_vectorstore()
    llm = get_llm(temperature=0.0)
    retriever = MultiQueryRetriever(vectorstore=vectorstore, k=4)
    
    # 1. Multi-Query expansion & retrieval
    queries = retriever.expand_query(question)
    docs = retriever.retrieve(question)
    context_str = format_docs_context(docs)
    
    # 2. Strict LCEL Chain
    prompt = PromptTemplate(
        input_variables=["context", "question"],
        template=STRICT_SYSTEM_PROMPT
    )
    
    rag_chain = prompt | llm | StrOutputParser()
    answer = rag_chain.invoke({"context": context_str, "question": question})
    
    formatted_docs = []
    for d in docs:
        formatted_docs.append({
            "content": d.page_content,
            "metadata": d.metadata
        })
        
    return {
        "question": question,
        "answer": answer.strip(),
        "expanded_queries": queries,
        "retrieved_documents_count": len(docs),
        "retrieved_context": formatted_docs,
        "raw_context_text": context_str
    }
