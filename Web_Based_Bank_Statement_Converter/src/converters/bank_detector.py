"""
Bank Detection Module
====================
Intelligent bank type detection from uploaded files.
"""

import os
import PyPDF2
import logging

class BankDetector:
    """Detects Albanian bank type from file content."""
    
    def __init__(self):
        self.bank_patterns = {
            'OTP': ['otp', 'otp bank', 'otp albania'],
            'BKT': ['bkt', 'banka kombetare tregtare', 'national commercial bank'],
            'RAIFFEISEN': ['raiffeisen', 'raiffeisen bank', 'rai bank'],
            'TIBANK': ['tibank', 'tabank', 'ti bank', 'tirana bank'],
            'UNION': ['union', 'union bank', 'banka union'],
            'EBILL': ['ebill', 'e-bill', 'electronic bill', 'fature elektronike']
        }
    
    def detect_bank(self, filepath):
        """
        Detect bank type from file content.
        
        Args:
            filepath (str): Path to the bank statement file
            
        Returns:
            str: Bank code (OTP, BKT, RAIFFEISEN, TIBANK, UNION, EBILL, or UNIVERSAL)
        """
        try:
            filename = os.path.basename(filepath).lower()
            
            # First check filename patterns
            for bank, patterns in self.bank_patterns.items():
                for pattern in patterns:
                    if pattern in filename:
                        return bank
            
            # Check file content based on extension
            if filepath.lower().endswith('.pdf'):
                return self._detect_from_pdf(filepath)
            elif filepath.lower().endswith(('.csv', '.txt')):
                return self._detect_from_text(filepath)
            
            # Default fallback
            return 'UNIVERSAL'
            
        except Exception as e:
            logging.error(f"Bank detection error: {e}")
            return 'UNIVERSAL'
    
    def _detect_from_pdf(self, filepath):
        """Detect bank from PDF content."""
        try:
            with open(filepath, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                # Extract text from first few pages
                text_content = ""
                for page_num in range(min(3, len(pdf_reader.pages))):
                    page = pdf_reader.pages[page_num]
                    text_content += page.extract_text().lower()
                
                # Check for bank patterns in content
                for bank, patterns in self.bank_patterns.items():
                    for pattern in patterns:
                        if pattern in text_content:
                            return bank
                
                return 'UNIVERSAL'
                
        except Exception as e:
            logging.error(f"PDF detection error: {e}")
            return 'UNIVERSAL'
    
    def _detect_from_text(self, filepath):
        """Detect bank from CSV/TXT content."""
        try:
            # Try different encodings
            encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
            
            for encoding in encodings:
                try:
                    with open(filepath, 'r', encoding=encoding) as file:
                        # Read first 2000 characters for detection
                        content = file.read(2000).lower()
                        
                        # Check for bank patterns
                        for bank, patterns in self.bank_patterns.items():
                            for pattern in patterns:
                                if pattern in content:
                                    return bank
                        
                        break  # If we successfully read the file, break
                        
                except UnicodeDecodeError:
                    continue  # Try next encoding
            
            return 'UNIVERSAL'
            
        except Exception as e:
            logging.error(f"Text detection error: {e}")
            return 'UNIVERSAL'
    
    def get_supported_banks(self):
        """Get list of supported banks."""
        return list(self.bank_patterns.keys()) + ['UNIVERSAL']