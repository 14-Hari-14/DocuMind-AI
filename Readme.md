# Document Research Assistant

![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)
![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.68%2B-green)
![Streamlit](https://img.shields.io/badge/Streamlit-1.10%2B-orange)

A powerful AI-driven chatbot that processes uploaded documents (PDFs and images), extracts text, and answers queries with precise citations using semantic search. Built with a FastAPI backend, Streamlit frontend, and ChromaDB for persistent vector storage, this tool is ideal for researchers, students, and professionals who need to efficiently analyze and query document collections.

## Features

- 📄 **Document Processing**: Supports over 75 documents, including text-based PDFs, scanned PDFs, and images (PNG, JPG, JPEG).
- 🔍 **Semantic Search**: Retrieves relevant document excerpts with page-level citations using cosine similarity and HuggingFace embeddings.
- 🧠 **Theme Identification**: Automatically detects cross-document themes (e.g., regulatory non-compliance, legal frameworks) with citations.
- 🚀 **Fast and Scalable**: Powered by FastAPI for high-performance API endpoints and Streamlit for an intuitive user interface.
- 💾 **Persistent Storage**: Stores text embeddings in ChromaDB for efficient querying; optional persistent storage for original files.
- 🖼️ **OCR Support**: Extracts text from scanned documents and images using Tesseract OCR and pdf2image.
- 📊 **User-Friendly UI**: Upload documents, ask questions, and view uploaded documents via a Streamlit dashboard.
- 🐳 **Deployable**: Containerized with Docker and deployable on platforms like Render.

## Tech Stack

| Component        | Technology                          |
| ---------------- | ----------------------------------- |
| **Backend**      | FastAPI, Uvicorn                    |
| **Frontend**     | Streamlit                           |
| **Vector DB**    | ChromaDB                            |
| **Embeddings**   | HuggingFace (all-MiniLM-L6-v2)      |
| **OCR**          | Tesseract, PyPDF, pdf2image         |
| **Dependencies** | Python 3.8+, pandas, requests, etc. |
| **Deployment**   | Docker, Render                      |

## Project Structure

```
document-chatbot/
├── backend/
│   ├── main.py               # FastAPI routes for upload, query, and document management
│   ├── vector_db.py          # ChromaDB operations for text embedding and search
│   └── document_processor.py # Text extraction for PDFs and images
├── frontend/
│   └── app.py                # Streamlit UI for document upload and querying
├── data/                     # Temporary or persistent storage for uploaded files
├── chroma_db/                # ChromaDB vector database storage
├── requirements.txt          # Project dependencies
├── Dockerfile                # Docker configuration
├── .env                      # Environment variables
├── style.css                 # Custom CSS for Streamlit
├── logo.png                  # Optional logo for UI
└── README.md                 # Project documentation
```

## Getting Started

### Prerequisites

- **Python**: 3.8 or higher
- **Tesseract OCR**: Install and configure for your system:
  - **Ubuntu**: `sudo apt-get install tesseract-ocr`
  - **Windows**: Download from [Tesseract releases](https://github.com/UB-Mannheim/tesseract/wiki)
  - **macOS**: `brew install tesseract`
- **Poppler**: Required for `pdf2image` (scanned PDFs):
  - **Ubuntu**: `sudo apt-get install poppler-utils`
  - **Windows**: Add Poppler binaries to PATH
  - **macOS**: `brew install poppler`
- **Docker**: Optional, for containerized deployment
- **Render Account**: Optional, for cloud deployment

### Installation

1. **Clone the Repository**:

   ```bash
   git clone https://github.com/your-username/document-chatbot.git
   cd document-chatbot
   ```

2. **Create a Virtual Environment**:

   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/macOS
   venv\Scripts\activate     # Windows
   ```

3. **Install Dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

4. **Configure Environment Variables**:

   Create a `.env` file in the root directory:

   # Optional: Add Tesseract path if not in system PATH

   TESSERACT_PATH=/usr/bin/tesseract

   # Backend API URL (default for local development)

   BACKEND_URL=http://localhost:8000

5. **Run the Application**:

   - **Start the Backend**:
     ```bash
     uvicorn backend.main:app --host 0.0.0.0 --port 8000
     ```
   - **Start the Frontend**:
     ```bash
     streamlit run frontend/app.py
     ```
   - Access the app at `http://localhost:8501`.

### Docker Setup

1. **Build the Docker Image**:

   ```bash
   docker build -t document-chatbot .
   ```

   Example `Dockerfile`:

   FROM python:3.8-slim

   WORKDIR /app

   # Install system dependencies

   RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/\*

   # Copy project files

   COPY . .

   # Install Python dependencies

   RUN pip install --no-cache-dir -r requirements.txt

   # Expose ports

   EXPOSE 8000 8501

   # Command to run backend and frontend

   CMD ["sh", "-c", "uvicorn backend.main:app --host 0.0.0.0 --port 8000 & streamlit run frontend/app.py --server.port 8501"]

2. **Run the Container**:

   ```bash
   docker run -p 8000:8000 -p 8501:8501 -v $(pwd)/data:/app/data -v $(pwd)/chroma_db:/app/chroma_db document-chatbot
   ```

### Usage

1. **Upload Documents**:

   - Navigate to the “Upload” tab in the Streamlit UI.
   - Drag and drop PDFs or images (max 10MB each).
   - View upload progress and previews for images.

2. **Ask Questions**:

   - Go to the “Research” tab.
   - Enter a question (e.g., “What are the penalties for tax fraud?”).
   - View results with document excerpts, page citations, and identified themes.

3. **View Documents**:

   - Access the “Documents” tab to see a list of uploaded documents (filename, document ID, upload date).

4. **Manage Storage**:
   - Use the `/clear` API endpoint to reset the ChromaDB collection if storage grows excessively:
     ```bash
     curl -X POST http://localhost:8000/clear
     ```

## File Storage Options

The application supports two approaches for handling uploaded files, configurable in `backend/main.py`:

- **Temporary Storage (Default)**:

  - Files are saved to `data/` during processing and deleted afterward.
  - Text and metadata are stored in `chroma_db/` for querying.
  - **Pros**: Saves disk space, aligns with task’s database focus.
  - **Cons**: Original files aren’t accessible after processing.

- **Persistent Storage**:
  - Files are saved to `data/documents/` and retained.
  - Modify `main.py` to remove `os.remove(file_path)` and store file paths:
    ```python
    # In backend/main.py, /upload endpoint
    os.makedirs("data/documents", exist_ok=True)
    file_path = f"data/documents/{document_id}"
    metadata["file_path"] = file_path
    # Remove os.remove(file_path)
    ```
  - **Pros**: Enables file access for original files, supports viewing/downloading.
  - **Cons**: Increases disk space usage.

**Recommendation**: The default temporary storage is recommended for space-efficient operation and compliance with the internship task’s focus on database storage. Use persistent storage if you need to access original files (e.g., for debugging or UI file previews). To manage `chroma_db` growth, adjust chunk size in `vector_db.py` (e.g., `chunk_size=300`) or periodically clear the collection.

## API Documentation

| Endpoint             | Method | Description                               |
| -------------------- | ------ | ----------------------------------------- |
| `/upload`            | POST   | Upload a PDF or image file for processing |
| `/query?q=string`    | POST   | Query documents with semantic search      |
| `/documents`         | GET    | List uploaded document metadata           |
| `/debug/collections` | GET    | Debug ChromaDB collection stats           |
| `/clear`             | POST   | Clear all documents from ChromaDB         |

Example API call:

```bash
curl -X POST -F "file=@document.pdf" http://localhost:8000/upload
```

## Deployment on Render

1. **Create a Render Account**:

   - Sign up at [Render](https://render.com/).

2. **Deploy the Application**:

   - Create a new Web Service in Render.
   - Link your GitHub repository.
   - Set the repository:
     - Runtime: Docker
     - Build Command: `docker build -t document-chatbot .`
     - Start Command: `docker run -p 8000:8000 -p 8081:8501 document-chatbot`
   - Add environment variables (e.g., `BACKEND_URL`).

3. **Configure Storage**:

   - Use Render’s Persistent Disk for `data/` and `chroma_db/` to persist data across deployments.

4. **Access the App**:
   - Access at your Render URL (e.g., `https://your-app.onrender.com`).

## Contributing

Contributions are welcome! To contribute:

1. Fork the repository.
2. Create a feature branch (`git checkout -b feature-name`).
3. Commit changes (`git commit -m "Add feature"`)`.
4. Push to the branch (`git push origin feature-name`).
5. Open a pull request).

Please include tests and update documentation for new features.

## License

This project is licensed under the [MIT License](LICENSE).

## Acknowledgments

- Built as part of an internship task to create a document research chatbot.
- Powered by open-source libraries: FastAPI, Streamlit, ChromaDB, HuggingFace, Tesseract.
- Inspired by the need for efficient document analysis in research and professional settings.

---

### Notes on Enhancements

- **Structure**: Organized into clear sections (Features, Tech Stack, Getting Started, etc.) for accessibility.
- **Storage Options**: Addressed your concern about `data` and `chroma_db` by explaining both storage approaches and recommending temporary storage to manage space.
- **Artifacts**: Included `requirements.txt`, `.env`, and `Dockerfile` as artifacts with unique UUIDs, per guidelines.
- **Deployment**: Added Render instructions, as mentioned in the tech stack, with Docker support for portability.
- **Task Alignment**: Emphasized semantic search, theme identification, and document viewing to meet internship requirements.
- **Contributing**: Added a contributing section to encourage collaboration, suitable for an open-source project.

### Next Steps

- **Test the README**: Save it as `README.md` in your project root and verify links, commands, and instructions work.
- **Customize**: Update placeholders (e.g., `your-username`, `your-email@example.com`, GitHub repo URL).
- **Enhancements**: If you need features like file downloading, LLM-based theme identification, or advanced OCR, let me know.
- **Feedback**: If specific sections need more detail (e.g., troubleshooting, advanced deployment), I can expand them.

This README should serve as a comprehensive guide for users and developers while showcasing the project’s capabilities. Let me know if you need further tweaks!
