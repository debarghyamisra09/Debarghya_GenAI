"""
Streamlit Frontend for Autonomous MirAI Student Policy Advisor
Provides:
- Interactive, responsive student chat interface
- PDF Document Ingest / Upload directly to FastAPI /ingest
- Multi-query expansion & retrieved context transparency
- Graceful error handling and timeout fallbacks
"""

import streamlit as st
import requests
import json
import os
import time

# Page configuration
st.set_page_config(
    page_title="MirAI Student Policy Advisor",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

# Custom CSS styling for premium feel
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1E3A8A;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1.05rem;
        color: #4B5563;
        margin-bottom: 1.5rem;
    }
    .guardrail-badge {
        display: inline-block;
        background-color: #ECFDF5;
        color: #065F46;
        border: 1px solid #A7F3D0;
        padding: 4px 12px;
        border-radius: 9999px;
        font-size: 0.82rem;
        font-weight: 600;
        margin-bottom: 1rem;
    }
    .context-box {
        background-color: #F8FAFC;
        border-left: 4px solid #3B82F6;
        padding: 12px 16px;
        border-radius: 4px;
        margin: 8px 0;
        font-size: 0.9rem;
    }
    .query-tag {
        background-color: #EEF2FF;
        color: #3730A3;
        padding: 3px 8px;
        border-radius: 6px;
        font-size: 0.8rem;
        margin: 2px;
        display: inline-block;
    }
</style>
""", unsafe_allow_html=True)

# Initialize Session State
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": "Hello! I am your **Autonomous MirAI Student Policy Advisor**. Ask me anything regarding academic regulations, attendance criteria, medical leave submission procedures, club guidelines, or campus disciplinary rules.",
            "sources": [],
            "expansions": []
        }
    ]

# Sidebar
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/graduation-cap.png", width=64)
    st.title("Policy Advisor Control")
    st.markdown("---")

    # Backend Connection Status Check
    backend_online = False
    try:
        health_resp = requests.get(f"{BACKEND_URL}/health", timeout=2)
        if health_resp.status_code == 200:
            backend_online = True
            st.success("🟢 Backend Service: Online (FastAPI)")
        else:
            st.warning("🟡 Backend Service: Degraded")
    except requests.exceptions.RequestException:
        st.error("🔴 Backend Service: Offline")
        st.caption(f"Could not connect to `{BACKEND_URL}`. Ensure `backend.py` is running.")

    st.markdown("---")
    st.subheader("📄 Document Ingestion")
    uploaded_file = st.file_uploader("Upload Handbook (PDF)", type=["pdf"])
    
    if uploaded_file is not None:
        if st.button("🚀 Ingest Document to ChromaDB", use_container_width=True):
            if backend_online:
                with st.spinner("Processing & vectorizing document..."):
                    try:
                        files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "application/pdf")}
                        response = requests.post(f"{BACKEND_URL}/ingest", files=files, timeout=60)
                        if response.status_code == 201:
                            data = response.json()
                            st.success(f"✅ Ingested {data['total_chunks']} chunks from {data['file_name']}!")
                        else:
                            st.error(f"Failed to ingest: {response.text}")
                    except Exception as e:
                        st.error(f"Ingestion error: {e}")
            else:
                # Direct local fallback ingestion
                try:
                    from rag_pipeline import ingest_pdf
                    import tempfile
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                        tmp.write(uploaded_file.getvalue())
                        tmp_path = tmp.name
                    res = ingest_pdf(tmp_path)
                    st.success(f"✅ Locally ingested {res['total_chunks']} chunks into ChromaDB!")
                    os.remove(tmp_path)
                except Exception as ex:
                    st.error(f"Local ingestion error: {ex}")

    st.markdown("---")
    st.subheader("🧪 Certification Test Prompts")
    test_prompts = [
        "I have 72% attendance. How many attendance marks will I get?",
        "I study at the Ratnam campus. I got sick and need medical leave. Who do I email and how many days do I have to submit my documents?",
        "We want to start a new Cybersecurity society under the Tech Club. Do we ask Management directly?",
        "How much is the fine for smoking a cigarette on campus?"
    ]

    for i, test_p in enumerate(test_prompts, 1):
        if st.button(f"Test {i}: {test_p[:35]}...", key=f"btn_test_{i}", use_container_width=True):
            st.session_state.current_prompt = test_p

    st.markdown("---")
    if st.button("🗑️ Clear Chat History", use_container_width=True):
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": "Chat history cleared. How can I assist you with MirAI institutional policies?",
                "sources": [],
                "expansions": []
            }
        ]
        st.rerun()

# Main Interface
st.markdown('<div class="main-header">Autonomous MirAI Student Policy Advisor</div>', unsafe_allow_html=True)
st.markdown('<div class="guardrail-badge">🛡️ Strict Zero-Hallucination Guardrails Active | Temperature: 0.0</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Official generative AI assistant for student regulations, leave procedures, attendance, and club governance.</div>', unsafe_allow_html=True)

# Render Chat History
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        
        # Display Query Expansions if present
        if msg.get("expansions"):
            with st.expander("🔍 Multi-Query Expansions Used for Retrieval", expanded=False):
                for exp in msg["expansions"]:
                    st.markdown(f'<span class="query-tag">{exp}</span>', unsafe_allow_html=True)
                    
        # Display Sources / Citations if present
        if msg.get("sources"):
            with st.expander(f"📚 Retrieved Handbook Clauses ({len(msg['sources'])} chunks)", expanded=False):
                for idx, src in enumerate(msg["sources"], 1):
                    src_meta = src.get("metadata", {})
                    source_file = src_meta.get("source_file", "Handbook")
                    page = src_meta.get("page", 0)
                    page_num = page + 1 if isinstance(page, int) else page
                    st.markdown(f"**Section {idx}** — *File:* `{source_file}` | *Page:* `{page_num}`")
                    st.markdown(f'<div class="context-box">{src.get("content", "")}</div>', unsafe_allow_html=True)

# Handle Input
prompt_input = st.chat_input("Ask a question about MirAI student policy...")

# Check if a test button was clicked
if "current_prompt" in st.session_state and st.session_state.current_prompt:
    prompt_input = st.session_state.current_prompt
    st.session_state.current_prompt = None

if prompt_input:
    # Add student message
    st.session_state.messages.append({"role": "user", "content": prompt_input})
    with st.chat_message("user"):
        st.markdown(prompt_input)

    # Generate assistant response
    with st.chat_message("assistant"):
        with st.spinner("Analyzing official policy handbook..."):
            answer_text = ""
            sources = []
            expansions = []
            
            # Send to FastAPI backend
            if backend_online:
                try:
                    payload = {"question": prompt_input}
                    resp = requests.post(f"{BACKEND_URL}/chat", json=payload, timeout=30)
                    if resp.status_code == 200:
                        data = resp.json()
                        answer_text = data["answer"]
                        sources = data.get("retrieved_context", [])
                        expansions = data.get("expanded_queries", [])
                    else:
                        answer_text = f"⚠️ Server Error ({resp.status_code}): {resp.text}"
                except requests.exceptions.Timeout:
                    answer_text = "⚠️ Request timed out. The server took too long to respond. Please try again."
                except requests.exceptions.ConnectionError:
                    answer_text = "⚠️ Connection to the backend server failed. Please check that FastAPI backend is running on port 8000."
                except Exception as e:
                    answer_text = f"⚠️ An unexpected error occurred: {str(e)}"
            else:
                # Direct local fallback execution
                try:
                    from rag_pipeline import query_policy
                    result = query_policy(prompt_input)
                    answer_text = result["answer"]
                    sources = result.get("retrieved_context", [])
                    expansions = result.get("expanded_queries", [])
                except Exception as ex:
                    answer_text = f"⚠️ Local RAG execution error: {str(ex)}"

            st.markdown(answer_text)
            
            # Display expansions
            if expansions:
                with st.expander("🔍 Multi-Query Expansions Used for Retrieval", expanded=False):
                    for exp in expansions:
                        st.markdown(f'<span class="query-tag">{exp}</span>', unsafe_allow_html=True)
                        
            # Display sources
            if sources:
                with st.expander(f"📚 Retrieved Handbook Clauses ({len(sources)} chunks)", expanded=False):
                    for idx, src in enumerate(sources, 1):
                        src_meta = src.get("metadata", {})
                        source_file = src_meta.get("source_file", "Handbook")
                        page = src_meta.get("page", 0)
                        page_num = page + 1 if isinstance(page, int) else page
                        st.markdown(f"**Section {idx}** — *File:* `{source_file}` | *Page:* `{page_num}`")
                        st.markdown(f'<div class="context-box">{src.get("content", "")}</div>', unsafe_allow_html=True)

            # Store in session state
            st.session_state.messages.append({
                "role": "assistant",
                "content": answer_text,
                "sources": sources,
                "expansions": expansions
            })
