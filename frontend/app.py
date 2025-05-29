import streamlit as st
import requests
from PIL import Image
import io
import logging
import pandas as pd

# Configure logging for frontend
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Config ---
st.set_page_config(page_title="DocuMind", page_icon="📚", layout="centered")
BACKEND_URL = "http://localhost:8000"

# --- Styles ---
def local_css(file_name):
    try:
        with open(file_name) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        logger.warning(f"style.css not found, skipping CSS")

local_css("style.css")

# --- Header ---
col1, col2 = st.columns([1, 4])
with col1:
    try:
        st.image("logo.png", width=80)
    except FileNotFoundError:
        st.write("Logo not found")
with col2:
    st.title("DocuMind AI")
    st.caption("Research documents in seconds")

# --- Sidebar ---
with st.sidebar:
    st.header("⚙️ Settings")
    api_key = st.text_input("API Key", type="password")
    st.markdown("---")
    st.info("Upload documents then ask questions in natural language.")

# --- Main Interface ---
tab1, tab2 = st.tabs(["📥 Upload", "🔍 Research"])

with tab1:
    st.subheader("Add Documents")
    uploaded_files = st.file_uploader(
        "Drag & drop files here",
        type=["pdf", "png", "jpg", "jpeg"],
        accept_multiple_files=True,
        help="Supports PDFs and images (scanned documents)"
    )
    
    if uploaded_files:
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for i, file in enumerate(uploaded_files):
            # Display file preview
            if file.type.startswith('image/'):
                img = Image.open(io.BytesIO(file.getvalue()))
                st.image(img, caption=file.name, width=200)
            
            # Upload to backend
            try:
                response = requests.post(
                    f"{BACKEND_URL}/upload",
                    files={"file": (file.name, file.getvalue(), file.type)},
                    timeout=30
                )
                
                if response.status_code == 201:
                    result = response.json()
                    st.success(f"Uploaded {file.name}: {result['chunks_stored']} chunks stored")
                    logger.info(f"Frontend: Successfully uploaded {file.name}")
                else:
                    error_detail = response.json().get("detail", response.text)
                    st.error(f"Failed to upload {file.name}: {response.status_code} - {error_detail}")
                    logger.error(f"Frontend: Upload failed for {file.name}: {response.status_code} - {error_detail}")
                
                progress_bar.progress((i + 1) / len(uploaded_files))
                status_text.text(f"Processed {i+1}/{len(uploaded_files)}: {file.name}")
            
            except requests.exceptions.RequestException as e:
                st.error(f"Failed to upload {file.name}: {str(e)}")
                logger.error(f"Frontend: Upload request failed for {file.name}: {str(e)}")
        
        if uploaded_files:
            st.success(f"✅ Processed {len(uploaded_files)} documents")

with tab2:
    st.subheader("Ask Anything")
    query = st.text_input("Your question", placeholder="e.g. What are the penalties for tax fraud?")
    
    if query:
        with st.spinner("Searching documents..."):
            try:
                response = requests.get(
                    f"{BACKEND_URL}/query",
                    params={"q": query},
                    timeout=30
                )
                
                if response.status_code == 200:
                    data = response.json()
                    results = data.get("results", [])
                    
                    if results:
                        st.subheader("📌 Answers")
                        # Prepare table data
                        table_data = []
                        for result in results:
                            filename = result["metadata"]["filename"]
                            answer = result["text"]
                            pages = result["pages"]
                            citation = ", ".join([f"page {p}" for p in pages])
                            table_data.append({
                                "Document": filename,  # Changed from "Doc Id" to "Document"
                                "Extracted answer": answer,
                                "Citation": citation
                            })
                        
                        # Display as a table
                        df = pd.DataFrame(table_data)
                        st.table(df)
                    else:
                        st.warning("No relevant results found")
                        logger.info(f"Frontend: No results for query: {query}")
                else:
                    st.error(f"Failed to process query: {response.status_code} - {response.text}")
                    logger.error(f"Frontend: Query failed: {response.status_code} - {response.text}")
                    
            except requests.exceptions.RequestException as e:
                st.error(f"Query request failed: {str(e)}")
                logger.error(f"Frontend: Query request failed: {str(e)}")