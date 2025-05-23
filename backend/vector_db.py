import logging
import os
from chromadb import PersistentClient
from chromadb.config import Settings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv
import re

logger = logging.getLogger(__name__)

load_dotenv()


class VectorDB:
    def __init__(self):
        try:
            self.client = PersistentClient(
                path="./chroma_db",
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
            # Temporary reset to clear corrupted state
            #self.client.reset()
            
            # Initialize local SentenceTransformer model
            self.embedding_fn = CustomEmbeddingFunction()
            logger.info("SentenceTransformer embedding function initialized successfully")
            
            self.collection = self.client.get_or_create_collection(
                name="documents",
                embedding_function=self.embedding_fn
            )
            
            self.text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=500,
                chunk_overlap=50,
                length_function=len,
                add_start_index=True
            )
            
            logger.info("VectorDB initialized successfully")
        except Exception as e:
            logger.error(f"VectorDB initialization failed: {str(e)}", exc_info=True)
            raise

    def add_document(self, text, metadata):
        try:
            if not text or len(text.strip()) < 10:
                logger.warning(f"Empty or too short text for document {metadata['document_id']}")
                return 0
            
            # Clean text to remove page markers and excessive newlines
            text = re.sub(r'\[Page \d+\]', '', text)
            text = re.sub(r'\n\s*\n', '\n', text)
            
            chunks = self.text_splitter.split_text(text)
            if not chunks:
                logger.warning(f"No chunks created for document {metadata['document_id']}: text length={len(text)}")
                return 0
            
            # Validate and clean chunks
            valid_chunks = []
            valid_indices = []
            for i, chunk in enumerate(chunks):
                if chunk and len(chunk.strip()) >= 10:
                    valid_chunks.append(chunk)
                    valid_indices.append(i)
                else:
                    logger.warning(f"Skipping invalid chunk {i} for document {metadata['document_id']}: {chunk[:50]}...")
            
            if not valid_chunks:
                logger.warning(f"No valid chunks after filtering for document {metadata['document_id']}")
                return 0
            
            ids = [f"{metadata['document_id']}_{i}" for i in valid_indices]
            metadatas = [
                {**metadata, "page": str(i+1), "chunk_id": i} for i in valid_indices
            ]
            
            logger.info(f"Adding {len(valid_chunks)} valid chunks for document {metadata['document_id']}")
            
            try:
                self.collection.add(
                    documents=valid_chunks,
                    metadatas=metadatas,
                    ids=ids
                )
                
                logger.info(f"Successfully stored {len(valid_chunks)} chunks for document {metadata['document_id']}")
                return len(valid_chunks)
            
            except Exception as e:
                logger.error(f"Embedding or storage failed for document {metadata['document_id']}: {str(e)}", exc_info=True)
                raise
            
        except Exception as e:
            logger.error(f"Failed to add document {metadata['document_id']}: {str(e)}", exc_info=True)
            raise Exception(f"VectorDB add_document failed: {str(e)}")

    def search(self, query, n_results=5):
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results
            )
            return results
        except Exception as e:
            logger.error(f"Search failed for query '{query}': {str(e)}", exc_info=True)
            raise

class CustomEmbeddingFunction:
    def __init__(self):
        try:
            self.model = SentenceTransformer('all-MiniLM-L6-v2')
            logger.info("Loaded SentenceTransformer model successfully")
        except Exception as e:
            logger.error(f"Failed to load SentenceTransformer model: {str(e)}", exc_info=True)
            raise
    
    def __call__(self, input):
        try:
            embeddings = self.model.encode(input, show_progress_bar=False)
            return embeddings.tolist()
        except Exception as e:
            logger.error(f"Local embedding failed: {str(e)}", exc_info=True)
            raise