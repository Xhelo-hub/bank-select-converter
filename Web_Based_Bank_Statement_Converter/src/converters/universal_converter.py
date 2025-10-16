"""
Universal Converter Module
=========================
Unified interface for all Albanian bank converters.
"""

import os
import subprocess
import sys
import shutil
import tempfile
from pathlib import Path
import logging

class UniversalConverter:
    """Universal converter that delegates to appropriate bank-specific converters."""
    
    def __init__(self, base_path=None):
        if base_path is None:
            # Default to parent directory where original converters are located
            self.base_path = Path(__file__).parent.parent.parent.parent
        else:
            self.base_path = Path(base_path)
        
        self.converters = {
            'OTP': 'OTP-2-QBO.py',
            'BKT': 'BKT-2-QBO.py',
            'RAIFFEISEN': 'RAI-2-QBO.py',
            'TIBANK': 'TIBANK-2-QBO.py',
            'UNION': 'UNION-2-QBO.py',
            'EBILL': 'Ebill-2-QBO (pdf-converter).py',
            'UNIVERSAL': 'ALL-BANKS-2-QBO.py'
        }
    
    def convert_file(self, filepath, bank_type='UNIVERSAL'):
        """
        Convert a bank statement file using appropriate converter.
        
        Args:
            filepath (str): Path to input file
            bank_type (str): Detected bank type
            
        Returns:
            str: Path to converted file or None if failed
        """
        try:
            # Get appropriate converter script
            converter_script = self.converters.get(bank_type, 'ALL-BANKS-2-QBO.py')
            converter_path = self.base_path / converter_script
            
            if not converter_path.exists():
                logging.error(f"Converter script not found: {converter_path}")
                # Fallback to universal converter
                converter_path = self.base_path / 'ALL-BANKS-2-QBO.py'
                
                if not converter_path.exists():
                    raise FileNotFoundError("No converter scripts found")
            
            # Create temporary directory for processing
            with tempfile.TemporaryDirectory() as temp_dir:
                # Copy file to base directory for processing
                filename = os.path.basename(filepath)
                temp_file = self.base_path / f'temp_{filename}'
                shutil.copy2(filepath, temp_file)
                
                try:
                    # Run the converter in the base directory
                    result = subprocess.run([
                        sys.executable, str(converter_path)
                    ], 
                    cwd=str(self.base_path),
                    capture_output=True, 
                    text=True,
                    timeout=300  # 5 minute timeout
                    )
                    
                    if result.returncode == 0:
                        # Find the output file in export directory
                        export_dir = self.base_path / 'export'
                        if export_dir.exists():
                            # Get the most recent CSV file
                            csv_files = list(export_dir.glob('*.csv'))
                            if csv_files:
                                # Sort by modification time and get the newest
                                newest_file = max(csv_files, key=lambda x: x.stat().st_mtime)
                                
                                # Create a copy in temp directory
                                output_file = Path(temp_dir) / newest_file.name
                                shutil.copy2(newest_file, output_file)
                                
                                # Move to final location (caller's responsibility)
                                final_output = self.base_path / 'converted' / newest_file.name
                                final_output.parent.mkdir(exist_ok=True)
                                shutil.copy2(output_file, final_output)
                                
                                return str(final_output)
                    else:
                        logging.error(f"Converter failed: {result.stderr}")
                        return None
                        
                finally:
                    # Clean up temp file
                    if temp_file.exists():
                        temp_file.unlink()
            
            return None
            
        except subprocess.TimeoutExpired:
            logging.error("Conversion timeout")
            return None
        except Exception as e:
            logging.error(f"Conversion error: {e}")
            return None
    
    def get_converter_info(self, bank_type):
        """Get information about a specific converter."""
        converter_script = self.converters.get(bank_type, 'ALL-BANKS-2-QBO.py')
        converter_path = self.base_path / converter_script
        
        return {
            'bank_type': bank_type,
            'script': converter_script,
            'exists': converter_path.exists(),
            'path': str(converter_path)
        }
    
    def list_available_converters(self):
        """List all available converters."""
        available = {}
        for bank_type, script in self.converters.items():
            converter_path = self.base_path / script
            available[bank_type] = {
                'script': script,
                'available': converter_path.exists()
            }
        return available