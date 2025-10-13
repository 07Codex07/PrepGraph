project:
  name: "PrepGraph"
  subtitle: "AI Chatbot with LangGraph + Hybrid RAG Memory"
  description: >
    PrepGraph is an AI-powered Retrieval-Augmented Generation (RAG) chatbot built using LangGraph, LangChain, FAISS, and Groq’s LLaMA-3.
    It understands your uploaded PDFs and PPTX files, retrieves the most relevant context, and chats naturally — 
    all while remembering your previous messages with persistent memory.

status:
  backend: "✅ Fully functional"
  frontend: "🚧 In progress (UI integration ongoing)"
  deployment: "🚀 Will be deployed once frontend workflow is complete"

features:
  - title: "🧠 Smart Conversational Memory"
    points:
      - "Each user gets their own persistent memory powered by SQLite"
      - "Remembers past messages and maintains coherent context"
      - "Local storage — no external database required"
  - title: "🔍 Hybrid RAG Retrieval"
    points:
      - "Combines BM25 (keyword-based) and FAISS (semantic embeddings)"
      - "Embeddings powered by SentenceTransformers"
      - "Supports PDFs and PPTX — great for lecture slides or reports"
      - "Detects subject (e.g., CN, DOS, SE) for more accurate retrieval"
  - title: "🤖 Groq LLaMA-3 Backend"
    points:
      - "Runs on Groq’s ultra-fast inference platform"
      - "Context-aware, structured, and concise answers"
      - "Uses robust response parsing and hallucination prevention"
  - title: "💬 Gradio Chat Interface"
    points:
      - "Clean and minimal chat UI"
      - "Automatically loads previous chat history"
      - "Includes clear input + one-click ‘Clear Chat’ button"
      - "Memory persists even after backend restart"
  - title: "⚙️ Developer Friendly"
    points:
      - "Separable modules for Memory, Retriever, and Graph logic"
      - "Cached FAISS + BM25 for instant reloads"
      - "Environment-driven configuration (.env)"
      - "Structured logging for production"

architecture:
  overview: |
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

project_structure:
  - "chatbot_graph.py        # Main Gradio app (UI + LangGraph)"
  - "chatbot_retriever.py    # Hybrid retriever (FAISS + BM25)"
  - "memory_store.py         # SQLite-based persistent message memory"
  - "data/                   # Folder for PDFs and PPTX files"
  - ".env                    # Stores API keys and configuration"
  - "requirements.txt"

use_cases:
  - "📚 Students → Ask questions directly from lecture notes or slides"
  - "💼 Professionals → Query or summarize project reports instantly"
  - "🤖 AI Enthusiasts → Learn LangGraph + RAG architecture in action"

setup_instructions:
  steps:
    - "1️⃣ Clone repository"
    - "```bash\ngit clone https://github.com/07Codex07/PrepGraph.git\ncd PrepGraph\n```"
    - "2️⃣ Create and activate virtual environment"
    - "```bash\npython -m venv myenv\nsource myenv/bin/activate  # or myenv\\Scripts\\activate (Windows)\n```"
    - "3️⃣ Install dependencies"
    - "```bash\npip install -r requirements.txt\n```"
    - "4️⃣ Add your Groq API key"
    - "```bash\necho \"GROQ_API_KEY=your_key_here\" > .env\n```"
    - "5️⃣ Run the app"
    - "```bash\npython chatbot_graph.py\n```"
    - "Visit http://127.0.0.1:7860 to start chatting!"

screenshots:
📸 Screenshots
<img width="1906" height="957" alt="Screenshot 1" src="https://github.com/user-attachments/assets/6a375518-536b-4dbf-b4e2-f6c79485fa03" /> <img width="1918" height="979" alt="Screenshot 2" src="https://github.com/user-attachments/assets/32b7780d-9a7a-417d-87f0-8a88d6a71983" /> <img width="1919" height="978" alt="Screenshot 3" src="https://github.com/user-attachments/assets/161bfacc-d212-431e-9cb9-b4d450eae5a1" />


future_plans:
  - "📝 Add DOCX and TXT file support"
  - "🎨 Themed Gradio UI + file upload preview"
  - "🧩 Extend memory window beyond last 3 messages"
  - "☁️ Deploy on Hugging Face Spaces or Vercel"
  - "📊 Integrate analytics and user tracking"

contributing:
  guidelines: >
    Pull requests are welcome!  
    For major changes, please open an issue first to discuss your ideas before implementing them.

credits:
  author: "Vinayak Sahu"
  github: "https://github.com/07Codex07"
  quote: "PrepGraph — where context meets intelligence."

⚡ Built with by Vinayak
