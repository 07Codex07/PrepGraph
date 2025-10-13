# ⚡ PrepGraph — AI Chatbot with LangGraph + Hybrid RAG Memory

PrepGraph is an **AI-powered RAG chatbot** built with **LangGraph, LangChain, FAISS, and Groq’s LLaMA-3**.  
It’s designed to **understand your uploaded PDFs/PPTX**, retrieve the most relevant context, and chat naturally — while remembering your past messages.  

---

## ✨ What Makes It Special

### 🧠 Smart Conversational Memory
- Each user has their own **persistent chat memory (SQLite-based)**  
- Remembers your last messages and maintains context automatically  
- Memory stored locally — no external database required  

### 🔍 Hybrid RAG Retrieval
- Combines **BM25 (keyword search)** + **FAISS (semantic embeddings)**  
- Embeddings generated using **SentenceTransformers**  
- Supports **both PDFs and PPTX** — ideal for lecture slides, project docs, or reports  
- Intelligent subject detection (CN, DOS, SE, etc.) for improved retrieval accuracy  

### 🤖 Groq LLaMA-3 Backend
- Powered by **Groq’s ultra-fast inference**  
- Context-aware and concise responses with safe fallback extraction  
- Strictly follows provided document context to avoid hallucination  

### 💬 Gradio Chat Interface
- Clean, responsive Gradio UI (minimal design)  
- Automatically loads your previous conversations  
- Includes “Send” + “Clear Chat” buttons for smooth interaction  
- Works even if backend restarts — chat memory persists!  

### ⚙️ Engineered for Developers
- Modular architecture: **Retriever**, **Memory**, and **Graph** layers separated  
- Cached **FAISS + BM25** indexes for lightning-fast reloads  
- `.env`-driven configuration for flexible environment setup  
- Structured logging and fault-tolerant persistence  
- Fully compatible with **Hugging Face Spaces** deployment  

---

## 🧩 Architecture Overview

```text
User Query → Memory (SQLite)
          ↓
      Retriever Node
     (BM25 + FAISS Hybrid)
          ↓
     Context Chunk
          ↓
      LLaMA-3 (Groq)
          ↓
    Answer + Memory Save
          ↓
     Gradio Chat UI
```

├── chatbot_graph.py        # Main Gradio app (UI + LangGraph)
├── chatbot_retriever.py    # Hybrid retriever (FAISS + BM25)
├── memory_store.py         # SQLite-based persistent memory
├── data/                   # Upload PDFs / PPTX here
├── .env                    # API keys and environment configs
└── requirements.txt


# 1️⃣ Clone the repository
git clone https://github.com/07Codex07/PrepGraph.git
cd PrepGraph

# 2️⃣ Create and activate virtual environment
python -m venv myenv
source myenv/bin/activate        # or myenv\Scripts\activate (Windows)

# 3️⃣ Install dependencies
pip install -r requirements.txt

# 4️⃣ Add your Groq API key
echo "GROQ_API_KEY=your_groq_api_key_here" > .env

# 5️⃣ Run the app
python chatbot_graph.py


🖼️ Screenshots

Chat UI	Document Context Retrieval	Response Generation
<img width="600" src="https://github.com/user-attachments/assets/6a375518-536b-4dbf-b4e2-f6c79485fa03">	<img width="600" src="https://github.com/user-attachments/assets/32b7780d-9a7a-417d-87f0-8a88d6a71983">	<img width="600" src="https://github.com/user-attachments/assets/161bfacc-d212-431e-9cb9-b4d450eae5a1">


🚀 Project Status

- Backend: Fully functional — LangGraph, Groq, FAISS, BM25, and SQLite memory integrated.
- Frontend: In progress — UI work ongoing (will connect to backend via Gradio/Bolt).
- Deployment: Will be deployed once frontend workflow is ready.

Built by Vinayak Sahu
