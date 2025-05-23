from fastapi import FastAPI, HTTPException, UploadFile, File
from .vector_db import VectorDB
import logging
import os
from .document_processor import extract_text_from_pdf

logger = logging.getLogger(__name__)
app = FastAPI()
vector_db = VectorDB()

@app.post("/upload/")
async def upload_file(file: UploadFile = File(...)):
    try:
        document_id = f"20250524_{int(os.times().elapsed):06d}"
        content = await file.read()
        # Save PDF to data folder
        os.makedirs("data", exist_ok=True)
        pdf_path = f"data/{document_id}_{file.filename}"
        with open(pdf_path, "wb") as f:
            f.write(content)
        # Extract text
        text = extract_text_from_pdf(pdf_path)
        metadata = {"document_id": document_id, "filename": file.filename}
        chunk_count = vector_db.add_document(text, metadata)
        logger.info(f"Successfully uploaded and stored {file.filename} with {chunk_count} chunks")
        return {"filename": file.filename, "chunk_count": chunk_count}, 201
    except Exception as e:
        logger.error(f"Upload failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/query/")
async def query(q: str, n_results: int = 5):
    try:
        results = vector_db.search(query=q, n_results=n_results)
        # Reformat ChromaDB response
        formatted_results = [
            {
                "text": doc,
                "metadata": meta,
                "distance": dist
            }
            for doc, meta, dist in zip(
                results.get("documents", [[]])[0],
                results.get("metadatas", [[]])[0],
                results.get("distances", [[]])[0]
            )
        ]
        logger.info(f"Query '{q}' returned {len(formatted_results)} results")
        return {"results": formatted_results}
    except Exception as e:
        logger.error(f"Search failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/debug/collections")
async def debug_collections():
    try:
        collection = vector_db.collection
        count = collection.count()
        samples = collection.peek(5)
        return {
            "count": count,
            "document_samples": samples.get("documents", [])
        }
    except Exception as e:
        logger.error(f"Debug failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))