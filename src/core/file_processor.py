"""
File processing module for handling multiple document formats.
"""

import os
import logging
import ebooklib
import pytesseract
import fitz  # PyMuPDF
from PIL import Image
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
from ebooklib import epub
from bs4 import BeautifulSoup
from docx import Document
from pdf2image import convert_from_path

class FileProcessor:
    """Handles document processing for multiple file formats."""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
        
    def process_file(self, file_path: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Process a document file and extract text.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Tuple of (success, message, extracted_data)
        """
        try:
            file_ext = Path(file_path).suffix.lower()
            
            if file_ext == '.docx':
                return self._process_docx(file_path)
            elif file_ext == '.pdf':
                return self._process_pdf(file_path)
            elif file_ext == '.epub':
                return self._process_epub(file_path)
            elif file_ext in ['.jpg', '.jpeg', '.png']:
                return self._process_image(file_path)
            elif file_ext == '.txt':
                return self._process_txt(file_path)
            else:
                return False, f"Unsupported file format: {file_ext}", None
                
        except Exception as e:
            self.logger.error(f"Error processing file {file_path}: {e}")
            return False, str(e), None
            
    def _process_docx(self, file_path: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Process DOCX file."""
        try:
            doc = Document(file_path)
            text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
            
            # Extract metadata
            metadata = {
                'title': doc.core_properties.title,
                'author': doc.core_properties.author,
                'created': doc.core_properties.created,
                'modified': doc.core_properties.modified
            }
            
            return True, "DOCX processed successfully", {
                'text': text,
                'metadata': metadata
            }
            
        except Exception as e:
            return False, f"Error processing DOCX: {e}", None
            
    def _process_pdf(self, file_path: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Process PDF file."""
        try:
            doc = fitz.open(file_path)
            text = ""
            metadata = {}
            
            # Extract text from each page
            for page in doc:
                text += page.get_text()
                
            # Extract metadata
            metadata = {
                'title': doc.metadata.get('title', ''),
                'author': doc.metadata.get('author', ''),
                'creation_date': doc.metadata.get('creationDate', ''),
                'modification_date': doc.metadata.get('modDate', '')
            }
            
            # Check if PDF is image-based
            if len(text.strip()) < 100:  # Arbitrary threshold
                # Convert PDF to images and perform OCR
                images = convert_from_path(file_path)
                ocr_text = ""
                for image in images:
                    ocr_text += pytesseract.image_to_string(image)
                text = ocr_text
                
            return True, "PDF processed successfully", {
                'text': text,
                'metadata': metadata
            }
            
        except Exception as e:
            return False, f"Error processing PDF: {e}", None
            
    def _process_epub(self, file_path: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Process EPUB file."""
        try:
            book = epub.read_epub(file_path)
            text = ""
            metadata = {}
            
            # Extract text from each document
            for doc in book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
                soup = BeautifulSoup(doc.content, 'html.parser')
                text += soup.get_text() + "\n"
                
            # Extract metadata
            metadata = {
                'title': book.get_metadata('DC', 'title')[0][0] if book.get_metadata('DC', 'title') else '',
                'author': book.get_metadata('DC', 'creator')[0][0] if book.get_metadata('DC', 'creator') else '',
                'language': book.get_metadata('DC', 'language')[0][0] if book.get_metadata('DC', 'language') else '',
                'publisher': book.get_metadata('DC', 'publisher')[0][0] if book.get_metadata('DC', 'publisher') else ''
            }
            
            return True, "EPUB processed successfully", {
                'text': text,
                'metadata': metadata
            }
            
        except Exception as e:
            return False, f"Error processing EPUB: {e}", None
            
    def _process_image(self, file_path: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Process image file using OCR."""
        try:
            image = Image.open(file_path)
            text = pytesseract.image_to_string(image)
            
            # Extract metadata
            metadata = {
                'format': image.format,
                'size': image.size,
                'mode': image.mode
            }
            
            return True, "Image processed successfully", {
                'text': text,
                'metadata': metadata
            }
            
        except Exception as e:
            return False, f"Error processing image: {e}", None
            
    def _process_txt(self, file_path: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Process plain text file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()
                
            return True, "Text file processed successfully", {
                'text': text,
                'metadata': {}
            }
            
        except Exception as e:
            return False, f"Error processing text file: {e}", None
            
    def get_supported_formats(self) -> List[str]:
        """Get list of supported file formats."""
        return [
            '.docx',  # Microsoft Word
            '.pdf',   # PDF
            '.epub',  # EPUB
            '.txt',   # Plain Text
            '.jpg',   # JPEG
            '.jpeg',  # JPEG
            '.png'    # PNG
        ] 