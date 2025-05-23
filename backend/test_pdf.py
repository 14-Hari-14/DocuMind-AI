# test_pdf.py
# Test different import methods for PyPDF2

import sys
print(f"Python version: {sys.version}")
print(f"Python path: {sys.path}")

# Try multiple import approaches
try:
    import PyPDF2
    print(f"Successfully imported PyPDF2 version: {PyPDF2.__version__}")
except ImportError as e:
    print(f"Failed to import PyPDF2: {e}")

try:
    from PyPDF2 import PdfReader
    print("Successfully imported PdfReader from PyPDF2")
except ImportError as e:
    print(f"Failed to import PdfReader from PyPDF2: {e}")

try:
    import pypdf
    print(f"Successfully imported pypdf version: {pypdf.__version__}")
except ImportError as e:
    print(f"Failed to import pypdf: {e}")

try:
    from pypdf import PdfReader as PypdfReader
    print("Successfully imported PdfReader from pypdf")
except ImportError as e:
    print(f"Failed to import PdfReader from pypdf: {e}")

print("\nTesting complete. Check the outputs above to determine which import method works.")