from pypdf import PdfReader
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
                reader = PdfReader(f)
                first_page_text = reader.pages[0].extract_text() or ""
                if len(first_page_text.strip()) > 50:
                    logger.info(f"PDF {pdf_path} detected as native (text extracted)")
                    return False
        except Exception as e:
            logger.warning(f"Text extraction check failed for {pdf_path}: {str(e)}")
        
        # Method 2: Image variance check
        try:
            images = convert_from_path(pdf_path, first_page=1, last_page=1, dpi=100)
            if not images:
                logger.warning(f"No images extracted from {pdf_path}")
                return True
                
            img_array = np.array(images[0].convert('L'))  # Convert to grayscale
            if np.std(img_array) > 25:  # Higher variance indicates text
                logger.info(f"PDF {pdf_path} detected as native (image variance)")
                return False
        except Exception as e:
            logger.warning(f"Image analysis check failed for {pdf_path}: {str(e)}")
        
        logger.info(f"PDF {pdf_path} detected as scanned")
        return True  # Default to scanned if checks are inconclusive
        
    except Exception as e:
        logger.error(f"PDF type detection failed for {pdf_path}: {str(e)}")
        return True  # Fallback to OCR processing

def pdf_to_images(pdf_path):
    """Convert PDF to high-res images for OCR with error handling"""
    try:
        images = convert_from_path(
            pdf_path,
            dpi=300,
            grayscale=True,
            thread_count=4,
            fmt='jpeg',
            poppler_path=None  # Add path if needed: e.g., r'/usr/local/bin'
        )
        logger.info(f"Converted {pdf_path} to {len(images)} images")
        return images
    except Exception as e:
        logger.error(f"PDF to image conversion failed for {pdf_path}: {str(e)}")
        raise

def process_scanned_pdf(pdf_path):
    """Robust OCR processing pipeline for scanned PDFs"""
    try:
        images = pdf_to_images(pdf_path)
        if not images:
            logger.warning(f"No images extracted from {pdf_path}")
            return ""
            
        text = []
        for page_num, img in enumerate(images, 1):
            try:
                ocr_text = pytesseract.image_to_string(
                    img,
                    config='--psm 6 -l eng+equ',
                    timeout=15
                )
                if ocr_text and ocr_text.strip():
                    text.append(f"[Page {page_num}]\n{ocr_text.strip()}")
                    logger.info(f"OCR extracted text from page {page_num} of {pdf_path}")
                else:
                    logger.warning(f"No text extracted from page {page_num} of {pdf_path}")
            except RuntimeError as e:
                logger.warning(f"OCR failed for page {page_num} of {pdf_path}: {str(e)}")
                continue
                
        extracted_text = '\n\n'.join(filter(None, text))
        logger.info(f"Extracted {len(extracted_text)} characters from scanned PDF {pdf_path}")
        return extracted_text
    except Exception as e:
        logger.error(f"Scanned PDF processing failed for {pdf_path}: {str(e)}")
        return ""

def extract_text_from_pdf(pdf_path):
    """Improved text extraction from native PDFs with page markers"""
    text = []
    try:
        with open(pdf_path, 'rb') as file:
            reader = PdfReader(file)
            for page_num, page in enumerate(reader.pages, 1):
                try:
                    page_text = page.extract_text()
                    if page_text and page_text.strip():
                        text.append(f"[Page {page_num}]\n{page_text.strip()}")
                        logger.info(f"Extracted text from page {page_num} of {pdf_path}")
                    else:
                        logger.warning(f"No text extracted from page {page_num} of {pdf_path}")
                except Exception as e:
                    logger.warning(f"Page {page_num} extraction failed for {pdf_path}: {str(e)}")
                    continue
                    
        extracted_text = '\n\n'.join(filter(None, text))
        logger.info(f"Extracted {len(extracted_text)} characters from native PDF {pdf_path}")
        return extracted_text
    except Exception as e:
        logger.error(f"PDF extraction failed for {pdf_path}: {str(e)}")
        return ""

def process_document(file_path):
    """Smart document processor with automatic type detection"""
    try:
        # Check file extension first
        if file_path.lower().endswith(('.png', '.jpg', '.jpeg')):
            try:
                text = pytesseract.image_to_string(Image.open(file_path))
                logger.info(f"Extracted {len(text)} characters from image {file_path}")
                # Print first 500 characters
                logger.info(f"First 500 characters of {file_path}:\n{text[:500] + '...' if len(text) > 500 else text}")
                return text
            except Exception as e:
                logger.error(f"Image processing failed for {file_path}: {str(e)}")
                return ""
        
        # Process PDF files
        if is_scanned_pdf(file_path):
            logger.info(f"Processing as scanned PDF: {file_path}")
            text = process_scanned_pdf(file_path)
        else:
            logger.info(f"Processing as native PDF: {file_path}")
            text = extract_text_from_pdf(file_path)
            
        # Print first 500 characters
        if text and text.strip():
            logger.info(f"First 500 characters of {file_path}:\n{text[:500] + '...' if len(text) > 500 else text}")
        else:
            logger.warning(f"No text extracted from {file_path}")
            
        return text
            
    except Exception as e:
        logger.error(f"Document processing failed for {file_path}: {str(e)}")
        return ""