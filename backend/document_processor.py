# backend/document_processor.py
from PyPDF2 import PdfReader  # Modern import style
from PIL import Image
import pytesseract
from pdf2image import convert_from_path
import numpy as np
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def is_scanned_pdf(pdf_path):
    """Check if PDF is scanned (image-based) using multiple detection methods"""
    try:
        # Method 1: Text extraction check
        try:
            with open(pdf_path, 'rb') as f:
                reader = PdfReader(f)  # Fixed: Use imported PdfReader directly
                first_page_text = reader.pages[0].extract_text() or ""
                if len(first_page_text.strip()) > 50:
                    return False
        except Exception as e:
            logger.warning(f"Text extraction check failed: {str(e)}")
        
        # Method 2: Image variance check
        try:
            images = convert_from_path(pdf_path, first_page=1, last_page=1, dpi=100)
            if not images:
                return True
                
            img_array = np.array(images[0].convert('L'))  # Convert to grayscale
            if np.std(img_array) > 25:  # Higher variance indicates text
                return False
        except Exception as e:
            logger.warning(f"Image analysis check failed: {str(e)}")
        
        return True  # Default to scanned if checks are inconclusive
        
    except Exception as e:
        logger.error(f"PDF type detection failed: {str(e)}")
        return True  # Fallback to OCR processing

def pdf_to_images(pdf_path):
    """Convert PDF to high-res images for OCR with error handling"""
    try:
        return convert_from_path(
            pdf_path,
            dpi=300,
            grayscale=True,
            thread_count=4,
            fmt='jpeg',
            poppler_path=None  # Add path if needed: r'/usr/local/bin'
        )
    except Exception as e:
        logger.error(f"PDF to image conversion failed: {str(e)}")
        raise

def process_scanned_pdf(pdf_path):
    """Robust OCR processing pipeline for scanned PDFs"""
    try:
        images = pdf_to_images(pdf_path)
        if not images:
            return ""
            
        text = []
        for img in images:
            try:
                ocr_text = pytesseract.image_to_string(
                    img,
                    config='--psm 6 -l eng+equ',
                    timeout=5  # Prevent hanging on difficult pages
                )
                text.append(ocr_text.strip())
            except RuntimeError as e:
                logger.warning(f"OCR failed for page: {str(e)}")
                continue
                
        return '\n'.join(filter(None, text))
    except Exception as e:
        logger.error(f"Scanned PDF processing failed: {str(e)}")
        return ""

def extract_text_from_pdf(pdf_path):
    """Improved text extraction from native PDFs"""
    text = []
    try:
        with open(pdf_path, 'rb') as file:
            reader = PdfReader(file)  # Fixed: Use imported PdfReader directly
            for page_num, page in enumerate(reader.pages, 1):
                try:
                    page_text = page.extract_text()
                    if page_text:
                        text.append(page_text.strip())
                except Exception as e:
                    logger.warning(f"Page {page_num} extraction failed: {str(e)}")
                    continue
                    
        return '\n\n'.join(filter(None, text))
    except Exception as e:
        logger.error(f"PDF extraction failed: {str(e)}")
        return ""

def process_document(file_path):
    """Smart document processor with automatic type detection"""
    try:
        # Check file extension first
        if file_path.lower().endswith(('.png', '.jpg', '.jpeg')):
            try:
                return pytesseract.image_to_string(Image.open(file_path))
            except Exception as e:
                logger.error(f"Image processing failed: {str(e)}")
                return ""
        
        # Process PDF files
        if is_scanned_pdf(file_path):
            logger.info(f"Processing as scanned PDF: {file_path}")
            return process_scanned_pdf(file_path)
        else:
            logger.info(f"Processing as native PDF: {file_path}")
            return extract_text_from_pdf(file_path)
            
    except Exception as e:
        logger.error(f"Document processing failed: {str(e)}")
        return ""