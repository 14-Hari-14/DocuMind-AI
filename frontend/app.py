import streamlit as st
import requests
from PIL import Image
import io

# --- Config ---
st.set_page_config(page_title="DocuMind", page_icon="📚", layout="centered")
BACKEND_URL = "http://localhost:8000"  # Change if deployed

# --- Styles ---
def local_css(file_name):
    with open(file_name) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

local_css("style.css")  # Create this file for custom styles

# --- Header ---
col1, col2 = st.columns([1, 4])
with col1:
    st.image("logo.png", width=80)  # Add your logo
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
            response = requests.post(
                f"{BACKEND_URL}/upload",
                files={"file": (file.name, file.getvalue())}
            )
            
            progress_bar.progress((i + 1) / len(uploaded_files))
            status_text.text(f"Processing {i+1}/{len(uploaded_files)}: {file.name}")
        
        st.success(f"✅ Processed {len(uploaded_files)} documents")

with tab2:
    st.subheader("Ask Anything")
    query = st.text_input("Your question", placeholder="e.g. What are the penalties for tax fraud?")
    
    if query:
        with st.spinner("Searching documents..."):
            response = requests.get(f"{BACKEND_URL}/query", params={"q": query})
            
            if response.status_code == 200:
                results = response.json().get("results", [])
                
                if results:
                    st.subheader("📌 Answers")
                    for result in results:
                        with st.expander(f"📄 {result['metadata']['filename']}"):
                            st.markdown(result['text'])
                            st.caption(f"🔗 Page {result['metadata'].get('page', 'N/A')}")
                else:
                    st.warning("No relevant results found")
            else:
                st.error("Failed to process query")