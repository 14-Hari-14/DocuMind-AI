from fastapi import FastAPI, UploadFile, File # To handle file uploads
from fastapi.middleware.cors import CORSMiddleware # To connect frontend and backend
import os 
from .document_processor import process_document # Custom component to process documents
from .vector_db import VectorDB # Wrapper for ChromaDB

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Lets any frontend access the backend
    allow_methods=["*"], # Allows all HTTP methods(GET, POST,  etc.)
)

vector_db = VectorDB() # Initialize the vector database

# Function to get data from doc
@app.post("/upload/")
async def upload_file(file: UploadFile = File(...)):
    file_path = f"data/{file.filename}"
    with open(file_path, "wb") as f:
        f.write(await file.read())
    
    text =  process_document(file_path) # Extracts text from the doc
    vector_db.add_document(text, metadata={"filename": file.filename}) # text -> vector -> vectordb
    
    return {"status": "success", "filename": file.filename} # Return success message with the filename


# Function to search the database and return top 5 matching chunks
@app.get("/query/")
async def query(q: str):
    results = vector_db.search(q, k = 5)
    return {"results": results} # Return the search results