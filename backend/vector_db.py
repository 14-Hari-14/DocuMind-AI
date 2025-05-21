# backend/vector_db.py
from langchain.text_splitter import RecursiveCharacterTextSplitter  # Correct import path
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
import os

class VectorDB:
    def __init__(self):
        # Initialize free Hugging Face embeddings
        self.embedding = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': False}  # Changed from True for stability
        )
        
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )
        
        self.db = Chroma(
            persist_directory="./chroma_db",
            embedding_function=self.embedding
        )
    
    def add_document(self, text, metadata):
        """Process and store document in ChromaDB"""
        chunks = self.text_splitter.split_text(text)
        self.db.add_texts(
            texts=chunks,
            metadatas=[metadata] * len(chunks)  # Same metadata for all chunks
        )
        self.db.persist()  # Optional: Save to disk
    
    def search(self, query, k=5):
        """Search for similar text chunks"""
        return self.db.similarity_search(query, k=k)