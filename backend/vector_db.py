import logging
import re
import time
from chromadb import PersistentClient
from chromadb.config import Settings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv
from typing import List, Dict, Optional
import numpy as np
import hashlib
from functools import lru_cache

logger = logging.getLogger(__name__)
load_dotenv()

class VectorDB:
    def __init__(self):
        try:
            self.client = PersistentClient(
                path="./chroma_db",
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=False,
                    is_persistent=True
                )
            )
            
            self.embedding_fn = OptimizedEmbeddingFunction()
            logger.info("Optimized embedding function initialized")
            
            # Validate or recreate collection
            try:
                self.collection = self.client.get_or_create_collection(
                    name="documents",
                    embedding_function=self.embedding_fn,
                    metadata={"hnsw:space": "cosine"}
                )
                # Check embedding dimension
                sample_embedding = self.embedding_fn(["test"])[0]
                expected_dim = len(sample_embedding)
                if self.collection.count() > 0:
                    peek_data = self.collection.peek(1)
                    stored_dim = len(peek_data["embeddings"][0]) if peek_data.get("embeddings") else expected_dim
                    if stored_dim != expected_dim:
                        logger.warning(f"Dimension mismatch: stored={stored_dim}, expected={expected_dim}. Resetting collection.")
                        self.client.delete_collection("documents")
                        self.collection = self.client.create_collection(
                            name="documents",
                            embedding_function=self.embedding_fn,
                            metadata={"hnsw:space": "cosine"}
                        )
            except Exception as e:
                logger.error(f"Collection initialization failed: {str(e)}. Creating new collection.")
                self.client.delete_collection("documents")
                self.collection = self.client.create_collection(
                    name="documents",
                    embedding_function=self.embedding_fn,
                    metadata={"hnsw:space": "cosine"}
                )
            
            self.text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=400,
                chunk_overlap=50,
                length_function=len,
                separators=["\n\n", "\n", ". ", "! ", "? ", " ", ""],
                keep_separator=True
            )
            
            logger.info(f"VectorDB initialized with {self.collection.count()} existing documents")
            
        except Exception as e:
            logger.error(f"VectorDB initialization failed: {str(e)}", exc_info=True)
            raise

    def _clean_and_validate_text(self, text: str) -> str:
        if not text:
            return ""
        text = re.sub(r'\s+', ' ', text.strip())
        text = re.sub(r'[^\w\s\.\,\!\?\-\:\;\(\)]', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        return text

    def _extract_page_from_chunk(self, chunk: str) -> str:
        page_match = re.search(r'\[Page\s+(\d+)\]', chunk)
        return page_match.group(1) if page_match else "1"

    def add_document(self, text: str, metadata: dict, page_texts: Dict[int, str] = None) -> int:
        try:
            if not text or len(text.strip()) < 20:
                logger.warning(f"Text too short for document {metadata.get('document_id', 'unknown')}")
                return 0
            
            cleaned_text = self._clean_and_validate_text(text)
            if not cleaned_text:
                logger.warning(f"No valid text after cleaning for {metadata.get('document_id')}")
                return 0
            
            chunks = self.text_splitter.split_text(cleaned_text)
            if not chunks:
                logger.warning(f"No chunks created for document {metadata.get('document_id')}")
                return 0
            
            batch_size = 10
            total_chunks_added = 0
            
            for i in range(0, len(chunks), batch_size):
                batch_chunks = chunks[i:i + batch_size]
                batch_ids = []
                batch_metadatas = []
                valid_batch_chunks = []
                
                for j, chunk in enumerate(batch_chunks):
                    if len(chunk.strip()) < 20:
                        continue
                    
                    chunk_id = f"{metadata['document_id']}_chunk_{i + j}"
                    page_num = self._extract_page_from_chunk(chunk)
                    
                    chunk_metadata = {
                        **metadata,
                        "chunk_id": chunk_id,
                        "page": page_num,
                        "chunk_index": i + j,
                        "text_length": len(chunk)
                    }
                    
                    batch_ids.append(chunk_id)
                    batch_metadatas.append(chunk_metadata)
                    valid_batch_chunks.append(chunk)
                
                if valid_batch_chunks:
                    try:
                        start_time = time.time()
                        self.collection.add(
                            documents=valid_batch_chunks,
                            metadatas=batch_metadatas,
                            ids=batch_ids
                        )
                        add_time = time.time() - start_time
                        total_chunks_added += len(valid_batch_chunks)
                        logger.info(f"Added batch {i//batch_size + 1}: {len(valid_batch_chunks)} chunks in {add_time:.2f}s")
                    except Exception as batch_error:
                        logger.error(f"Failed to add batch {i//batch_size + 1}: {str(batch_error)}")
                        continue
            
            logger.info(f"Successfully added {total_chunks_added} chunks for document {metadata.get('document_id')}")
            return total_chunks_added
            
        except Exception as e:
            logger.error(f"Failed to add document {metadata.get('document_id', 'unknown')}: {str(e)}", exc_info=True)
            raise

    def search(self, query: str, n_results: int = 3) -> dict:  # Changed to 3
        try:
            if not query.strip():
                return {"documents": [], "metadatas": [], "distances": [], "ids": [], "pages": []}
            
            cleaned_query = self._clean_and_validate_text(query)
            if not cleaned_query:
                logger.warning("Query became empty after cleaning")
                return {"documents": [], "metadatas": [], "distances": [], "ids": [], "pages": []}
            
            start_time = time.time()
            search_results = self.collection.query(
                query_texts=[cleaned_query],
                n_results=n_results,  # Reduced for speed
                include=["documents", "metadatas", "distances"]
            )
            query_time = time.time() - start_time
            logger.info(f"Vector search took {query_time:.2f}s for query: '{query[:50]}...'")
            
            if not search_results["documents"] or not search_results["documents"][0]:
                logger.info(f"No results found for query: {query}")
                return {"documents": [], "metadatas": [], "distances": [], "ids": [], "pages": []}
            
            processed_results = self._process_search_results(search_results, n_results, query)
            logger.info(f"Returning {len(processed_results['documents'])} unique results")
            return processed_results
            
        except Exception as e:
            logger.error(f"Search failed for query '{query}': {str(e)}", exc_info=True)
            raise

    def _process_search_results(self, raw_results: dict, n_results: int, original_query: str) -> dict:
        try:
            documents = raw_results["documents"][0]
            metadatas = raw_results["metadatas"][0]
            distances = raw_results["distances"][0]
            
            seen_content = set()
            seen_docs = {}
            unique_results = {
                "documents": [],
                "metadatas": [],
                "distances": [],
                "ids": [],
                "pages": []
            }
            
            for doc, meta, dist in zip(documents, metadatas, distances):
                content_hash = hashlib.md5(doc.encode()).hexdigest()
                doc_id = meta.get("document_id", "unknown")
                
                if content_hash in seen_content:
                    continue
                if doc_id in seen_docs and seen_docs[doc_id] >= 2:
                    continue
                if dist > 0.8:
                    continue
                
                seen_content.add(content_hash)
                seen_docs[doc_id] = seen_docs.get(doc_id, 0) + 1
                
                unique_results["documents"].append(doc)
                unique_results["metadatas"].append(meta)
                unique_results["distances"].append(dist)
                unique_results["ids"].append(meta.get("chunk_id", ""))
                unique_results["pages"].append([meta.get("page", "1")])
                
                if len(unique_results["documents"]) >= n_results:
                    break
            
            return unique_results
            
        except Exception as e:
            logger.error(f"Failed to process search results: {str(e)}")
            raise

    def get_collection_stats(self) -> dict:
        try:
            count = self.collection.count()
            return {
                "total_documents": count,
                "collection_name": self.collection.name,
                "embedding_model": "sentence-transformers/all-MiniLM-L6-v2"
            }
        except Exception as e:
            logger.error(f"Failed to get collection stats: {str(e)}")
            return {"error": str(e)}

class OptimizedEmbeddingFunction:
    def __init__(self):
        try:
            model_name = 'sentence-transformers/all-MiniLM-L6-v2'
            self.model = SentenceTransformer(model_name)
            self.model.max_seq_length = 256
            logger.info(f"Loaded optimized embedding model: {model_name}")
        except Exception as e:
            logger.error(f"Failed to load embedding model: {str(e)}", exc_info=True)
            raise
    
    @lru_cache(maxsize=1000)
    def _cached_encode(self, text: str) -> tuple:
        try:
            embedding = self.model.encode([text], show_progress_bar=False, convert_to_tensor=False)[0]
            return tuple(embedding.tolist())
        except Exception as e:
            logger.error(f"Encoding failed for text: {text[:50]}... Error: {str(e)}")
            raise
    
    def __call__(self, input: List[str]) -> List[List[float]]:
        try:
            if not input:
                return []
            
            start_time = time.time()
            if len(input) <= 5:
                embeddings = [list(self._cached_encode(text)) for text in input]
            else:
                embeddings = self.model.encode(
                    input, 
                    show_progress_bar=False, 
                    convert_to_tensor=False,
                    batch_size=16
                ).tolist()
            
            encode_time = time.time() - start_time
            logger.info(f"Encoded {len(input)} texts in {encode_time:.2f}s")
            return embeddings
            
        except Exception as e:
            logger.error(f"Batch embedding failed: {str(e)}", exc_info=True)
            raise