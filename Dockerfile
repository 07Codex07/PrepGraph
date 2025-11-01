# -----------------------------
# Dockerfile for PrepGraph backend
# -----------------------------
    FROM python:3.10-slim

    # Set working directory inside container
    WORKDIR /app
    
    # Copy everything into the container
    COPY . /app
    
    # Install system dependencies for FAISS + PDF + PPTX
    RUN apt-get update && apt-get install -y \
        build-essential \
        poppler-utils \
        libgl1 \
        && rm -rf /var/lib/apt/lists/*
    
    # Install Python dependencies
    RUN pip install --no-cache-dir -U pip && \
        pip install --no-cache-dir \
            fastapi uvicorn[standard] python-dotenv \
            tiktoken rank-bm25 langchain langchain-community langchain-core \
            langchain-groq sentence-transformers faiss-cpu gradio numpy
    
    # Expose FastAPI port
    EXPOSE 8000
    
    # Environment variables
    ENV HOST=0.0.0.0
    ENV PORT=8000
    
    # Command to run app
    CMD ["python", "main_api.py"]
    
