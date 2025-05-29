# main.py
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import logging
import os
import pypdf
import pytesseract
from PIL import Image
import io
import time  # Added missing import
from .vector_db import VectorDB
from .document_processor import extract_text_from_pdf
from datetime import datetime
import re
from typing import List

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(title="DocuMind API", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize VectorDB
vector_db = VectorDB()

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    try:
        if not file.filename:
            raise HTTPException(status_code=400, detail="No filename provided")
        
        # Validate file type
        allowed_extensions = {'.pdf', '.png', '.jpg', '.jpeg'}
        file_ext = os.path.splitext(file.filename)[1].lower()
        if file_ext not in allowed_extensions:
            raise HTTPException(status_code=400, detail=f"Unsupported file type. Allowed: {', '.join(allowed_extensions)}")
        
        # Check file size (10MB limit)
        content = await file.read()
        if len(content) > 10 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="File too large. Maximum size is 10MB")
        
        # Generate unique document ID
        document_id = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}"
        
        # Save file temporarily
        os.makedirs("data", exist_ok=True)
        file_path = f"data/{document_id}"
        with open(file_path, "wb") as f:
            f.write(content)
        
        # Extract text
        start_time = time.time()
        text = extract_text_from_pdf(file_path)
        extract_time = time.time() - start_time
        logger.info(f"Text extraction for {file.filename} took {extract_time:.2f}s")
        
        if not text:
            os.remove(file_path)
            raise HTTPException(status_code=400, detail="No text extracted from file")
        
        # Store in VectorDB
        metadata = {
            "document_id": document_id,
            "filename": file.filename,
            "upload_date": datetime.now().isoformat()
        }
        start_time = time.time()
        chunk_count = vector_db.add_document(text, metadata)
        store_time = time.time() - start_time
        logger.info(f"Storing {file.filename} with {chunk_count} chunks took {store_time:.2f}s")
        
        # Clean up
        if os.path.exists(file_path):
            os.remove(file_path)
        
        logger.info(f"Successfully uploaded {file.filename}: {chunk_count} chunks")
        return JSONResponse(
            content={
                "filename": file.filename,
                "document_id": document_id,
                "chunks_stored": chunk_count
            },
            status_code=201
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload failed for {file.filename}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)

@app.get("/query")
async def query(q: str, n_results: int = 3):
    try:
        if not q.strip():
            raise HTTPException(status_code=400, detail="Query cannot be empty")
        
        start_time = time.time()
        results = vector_db.search(query=q.strip(), n_results=n_results)
        search_time = time.time() - start_time
        logger.info(f"Search for '{q}' took {search_time:.2f}s")
        
        # Theme identification
        themes = []
        if results["documents"]:
            theme_keywords = {
                "Regulatory Non-Compliance": ["non-compliance", "violation", "regulation", "SEBI", "LODR"],
                "Penalty Justification": ["penalty", "fine", "sanction", "statutory"],
                "Legal Framework": ["act", "law", "clause", "section"]
            }
            for theme, keywords in theme_keywords.items():
                citations = []
                for i, doc in enumerate(results["documents"]):
                    if any(keyword.lower() in doc.lower() for keyword in keywords):
                        citation = f"{results['metadatas'][i]['filename']} (page {', '.join(results['pages'][i])})"
                        citations.append(citation)
                if citations:
                    themes.append({
                        "name": theme,
                        "description": f"Documents discussing {theme.lower()}.",
                        "citations": citations[:3]
                    })
        
        formatted_results = [
            {
                "text": doc,
                "metadata": meta,
                "pages": pages,
                "relevance_score": round(1 - float(dist), 3)
            }
            for doc, meta, pages, dist in zip(
                results["documents"], results["metadatas"], results["pages"], results["distances"]
            )
        ]
        
        logger.info(f"Query '{q}' returned {len(formatted_results)} results")
        return {
            "results": formatted_results,
            "themes": themes
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Search failed for query '{q}': {str(e)}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@app.get("/debug/collections")
async def debug_collections():
    try:
        count = vector_db.collection.count()
        samples = vector_db.collection.peek(3)
        return {
            "document_count": count,
            "sample_documents": [doc[:100] + "..." if len(doc) > 100 else doc for doc in samples.get("documents", [])],
            "sample_metadata": samples.get("metadatas", [])
        }
    except Exception as e:
        logger.error(f"Debug failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Debug failed: {str(e)}")