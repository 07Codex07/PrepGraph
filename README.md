# PrepGraph (AI Chatbot with LangGraph + Gradio)

🚀 An AI-powered chatbot that uses LangGraph, LangChain, and Groq’s LLaMA 3 to answer user queries.
Supports document-based RAG (PDF, PPTX) and a Gradio frontend for interaction.

✨ Features

🔗 LangGraph pipeline with retrieval + chat nodes

📄 RAG support: Upload PDFs / PPTX → indexed with FAISS

🤖 Groq LLaMA 3 model as the LLM backend

🧠 Context-aware replies (last 2 user messages only)

🎨 Simple Gradio interface for chatting with your bot

⚡ Lightweight + avoids leaking secrets (.env ignored by git)

📂 Project Structure
Chatbot/
│── app.py           # Gradio frontend
│── chatbot.py       # Chatbot logic (LangGraph pipeline)
│── README.md        # Project docs

🛠️ Requirements

Python 3.10+

LangChain

LangGraph

Groq API

FAISS

Gradio

⚙️ Setup

Clone repo

git clone https://github.com/07Codex07/PrepGraph.git
cd PrepGraph


Create virtual env & install deps

python -m venv myenv
myenv\Scripts\activate   # (Windows)
# OR source myenv/bin/activate (Linux/Mac)

pip install -r requirements.txt


Create .env file

GROQ_API_KEY=your_groq_api_key_here

🚀 Run the app
python app.py


Then open the Gradio link (usually http://127.0.0.1:7860/
) in your browser.

📸 Screenshots

<img width="1906" height="957" alt="Screenshot 2025-08-26 014202" src="https://github.com/user-attachments/assets/6a375518-536b-4dbf-b4e2-f6c79485fa03" />
<img width="1918" height="979" alt="Screenshot 2025-08-26 014643" src="https://github.com/user-attachments/assets/32b7780d-9a7a-417d-87f0-8a88d6a71983" />
<img width="1919" height="978" alt="Screenshot 2025-08-26 014759" src="https://github.com/user-attachments/assets/161bfacc-d212-431e-9cb9-b4d450eae5a1" />


📌 Notes

By default, .env, myenv/, and __pycache__/ are ignored by git.

Keep your Groq API key private.

⚡ Built with ❤️ by Vinayak
