# PrepGraph (AI Chatbot with LangGraph + Gradio)

🚀 PrepGraph is an AI-powered chatbot built with LangGraph, LangChain, and Groq’s LLaMA 3.
It supports document-based RAG (PDF, PPTX) and comes with a Gradio frontend for seamless interaction.

-----------✨ Features------------

🔗 LangGraph pipeline with retrieval + chat nodes

📄 RAG support → Upload PDFs / PPTX → indexed with FAISS

🤖 Groq LLaMA 3 model as the LLM backend

🧠 Context-aware replies (remembers last 2 user messages)

🎨 Gradio Web App → clean, interactive chatbot UI

⚡ Lightweight & secure → .env ignored by Git

📊 Easily extensible → can be deployed on Hugging Face Spaces

-----------📊 Example Use Case-------

📚 Students → Ask questions directly from lecture slides / PDFs

💼 Professionals → Summarize reports and query project docs

🤖 AI learners → Understand LangGraph pipelines through an end-to-end example

-------------🔍 How It Works (Architecture)----------

Document Ingestion → PDFs / PPTX loaded via LangChain loaders

Indexing → Text chunks embedded + stored in FAISS vector DB

Graph Execution (LangGraph) →

Retrieval Node (fetch relevant context)

Chat Node (Groq LLaMA 3 generates response)

Conversation Context → Keeps last 2 user messages for coherence

Frontend → Gradio-based chatbot interface



[User Query in Gradio] → [LangGraph Pipeline] → [Retriever + FAISS] → [Groq LLaMA 3] → [Response in Gradio]



----------📂 Project Structure--------
<img width="502" height="119" alt="image" src="https://github.com/user-attachments/assets/4476512c-e386-4f47-b206-a4b721a15619" />

------🛠️ Requirements--------

Python 3.10+


LangChain

LangGraph

Groq API

FAISS

Gradio

-----------⚙️ Setup-------

1. Clone repo

git clone https://github.com/07Codex07/PrepGraph.git

cd PrepGraph

2. Create virtual env & install deps

python -m venv myenv

myenv\Scripts\activate   # (Windows)

# OR

source myenv/bin/activate   # (Linux/Mac)

pip install -r requirements.txt

3. Create .env file

GROQ_API_KEY=your_groq_api_key_here

4. Run the Gradio app

python app.py



-------------🧪 Demo Queries-------------

Q: Summarize this uploaded PDF in 3 bullet points.

Q: What are the important questions from the pyqs of computer network?

Q: Based on the last 2 chats, suggest a follow-up question.

📸 Screenshots
<img width="1906" height="957" alt="Screenshot 1" src="https://github.com/user-attachments/assets/6a375518-536b-4dbf-b4e2-f6c79485fa03" /> <img width="1918" height="979" alt="Screenshot 2" src="https://github.com/user-attachments/assets/32b7780d-9a7a-417d-87f0-8a88d6a71983" /> <img width="1919" height="978" alt="Screenshot 3" src="https://github.com/user-attachments/assets/161bfacc-d212-431e-9cb9-b4d450eae5a1" />

-----------🚀 Roadmap / Future Improvements-------------

 Add support for DOCX / TXT uploads
 Improve Gradio UI (themes, file upload preview, streaming responses)
 Extend chat memory beyond 2 messages
 Deploy to Hugging Face Spaces / Vercel for easy sharing
 Add user analytics (track usage & requests)

-----------🤝 Contributing---------

Pull requests are welcome! For major changes, please open an issue first to discuss what you’d like to change.


⚡ Built with by Vinayak
