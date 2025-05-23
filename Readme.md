# Document Research Assistant

An AI-powered chatbot that processes uploaded documents, extracts text, and answers questions with citations using semantic search.

## Features

- 📄 Process 75+ documents (PDFs, scanned images)
- 🔍 Semantic search with page/paragraph citations
- 🧠 Identify cross-document themes
- 🚀 FastAPI backend + Streamlit frontend
- 💾 Persistent ChromaDB vector storage

## Tech Stack

| Component  | Technology                     |
| ---------- | ------------------------------ |
| Backend    | FastAPI, Uvicorn               |
| Frontend   | Streamlit                      |
| Vector DB  | ChromaDB                       |
| Embeddings | HuggingFace (all-MiniLM-L6-v2) |
| OCR        | Tesseract, PyPDF2              |
| Deployment | Docker, Render                 |

## Project Structure

![alt text](image.png)

## License

MIT License
