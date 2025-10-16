"""
File Manager Module
==================
Handles file operations, cleanup, and security.
"""

import os
import shutil
import time
from datetime import datetime, timedelta
from pathlib import Path
import hashlib
import logging

class FileManager:
    """Manages file operations for the bank converter API."""
    
    def __init__(self, upload_dir='uploads', converted_dir='converted'):
        self.upload_dir = Path(upload_dir)
        self.converted_dir = Path(converted_dir)
        
        # Create directories if they don't exist
        self.upload_dir.mkdir(exist_ok=True)
        self.converted_dir.mkdir(exist_ok=True)
    
    def save_uploaded_file(self, file, job_id):
        """
        Save uploaded file with secure naming.
        
        Args:
            file: Werkzeug FileStorage object
            job_id (str): Unique job identifier
            
        Returns:
            str: Path to saved file
        """
        try:
            # Create secure filename
            filename = self._secure_filename(file.filename)
            filepath = self.upload_dir / f'{job_id}_{filename}'
            
            # Save file
            file.save(str(filepath))
            
            # Log file info
            file_size = filepath.stat().st_size
            logging.info(f"File uploaded: {filename}, Size: {file_size} bytes, Job: {job_id}")
            
            return str(filepath)
            
        except Exception as e:
            logging.error(f"File save error: {e}")
            raise
    
    def move_converted_file(self, source_path, job_id, original_filename):
        """
        Move converted file to converted directory.
        
        Args:
            source_path (str): Path to source file
            job_id (str): Job identifier
            original_filename (str): Original filename for reference
            
        Returns:
            str: Path to moved file
        """
        try:
            source_file = Path(source_path)
            if not source_file.exists():
                raise FileNotFoundError(f"Source file not found: {source_path}")
            
            # Create destination filename
            dest_filename = f'{job_id}_{source_file.name}'
            dest_path = self.converted_dir / dest_filename
            
            # Move file
            shutil.move(str(source_file), str(dest_path))
            
            logging.info(f"File converted: {original_filename} -> {dest_filename}")
            return str(dest_path)
            
        except Exception as e:
            logging.error(f"File move error: {e}")
            raise
    
    def get_file_info(self, filepath):
        """Get file information."""
        try:
            file_path = Path(filepath)
            if not file_path.exists():
                return None
            
            stat = file_path.stat()
            return {
                'name': file_path.name,
                'size': stat.st_size,
                'created': datetime.fromtimestamp(stat.st_ctime),
                'modified': datetime.fromtimestamp(stat.st_mtime),
                'extension': file_path.suffix.lower()
            }
            
        except Exception as e:
            logging.error(f"File info error: {e}")
            return None
    
    def cleanup_old_files(self, max_age_hours=1):
        """
        Clean up files older than specified age.
        
        Args:
            max_age_hours (int): Maximum age in hours
            
        Returns:
            dict: Cleanup statistics
        """
        cutoff_time = time.time() - (max_age_hours * 3600)
        stats = {'removed': 0, 'errors': 0, 'total_size': 0}
        
        # Clean upload directory
        stats.update(self._cleanup_directory(self.upload_dir, cutoff_time))
        
        # Clean converted directory  
        converted_stats = self._cleanup_directory(self.converted_dir, cutoff_time)
        stats['removed'] += converted_stats['removed']
        stats['errors'] += converted_stats['errors']
        stats['total_size'] += converted_stats['total_size']
        
        if stats['removed'] > 0:
            logging.info(f"Cleanup completed: {stats['removed']} files removed, "
                        f"{stats['total_size']} bytes freed")
        
        return stats
    
    def _cleanup_directory(self, directory, cutoff_time):
        """Clean up a specific directory."""
        stats = {'removed': 0, 'errors': 0, 'total_size': 0}
        
        try:
            for file_path in directory.iterdir():
                if file_path.is_file():
                    try:
                        if file_path.stat().st_mtime < cutoff_time:
                            file_size = file_path.stat().st_size
                            file_path.unlink()
                            stats['removed'] += 1
                            stats['total_size'] += file_size
                    except Exception as e:
                        logging.error(f"Error removing {file_path}: {e}")
                        stats['errors'] += 1
                        
        except Exception as e:
            logging.error(f"Directory cleanup error: {e}")
            stats['errors'] += 1
        
        return stats
    
    def _secure_filename(self, filename):
        """Create a secure filename."""
        # Remove path components and dangerous characters
        filename = os.path.basename(filename)
        filename = ''.join(c for c in filename if c.isalnum() or c in '.-_')
        
        # Limit length
        if len(filename) > 100:
            name, ext = os.path.splitext(filename)
            filename = name[:100-len(ext)] + ext
        
        return filename or 'unnamed_file'
    
    def validate_file(self, filepath, max_size_mb=50):
        """
        Validate uploaded file.
        
        Args:
            filepath (str): Path to file
            max_size_mb (int): Maximum size in MB
            
        Returns:
            dict: Validation result
        """
        try:
            file_path = Path(filepath)
            
            if not file_path.exists():
                return {'valid': False, 'error': 'File not found'}
            
            # Check file size
            size_mb = file_path.stat().st_size / (1024 * 1024)
            if size_mb > max_size_mb:
                return {'valid': False, 'error': f'File too large: {size_mb:.1f}MB > {max_size_mb}MB'}
            
            # Check file extension
            allowed_extensions = {'.pdf', '.csv', '.txt'}
            if file_path.suffix.lower() not in allowed_extensions:
                return {'valid': False, 'error': f'Invalid file type: {file_path.suffix}'}
            
            # Check if file is readable
            try:
                with open(file_path, 'rb') as f:
                    f.read(1024)  # Try to read first 1KB
            except Exception:
                return {'valid': False, 'error': 'File is not readable or corrupted'}
            
            return {'valid': True, 'size_mb': size_mb, 'extension': file_path.suffix}
            
        except Exception as e:
            return {'valid': False, 'error': str(e)}
    
    def get_storage_stats(self):
        """Get storage statistics."""
        try:
            upload_stats = self._get_directory_stats(self.upload_dir)
            converted_stats = self._get_directory_stats(self.converted_dir)
            
            return {
                'upload_dir': upload_stats,
                'converted_dir': converted_stats,
                'total_files': upload_stats['files'] + converted_stats['files'],
                'total_size_mb': (upload_stats['size'] + converted_stats['size']) / (1024 * 1024)
            }
            
        except Exception as e:
            logging.error(f"Storage stats error: {e}")
            return {}
    
    def _get_directory_stats(self, directory):
        """Get statistics for a directory."""
        stats = {'files': 0, 'size': 0}
        
        try:
            for file_path in directory.iterdir():
                if file_path.is_file():
                    stats['files'] += 1
                    stats['size'] += file_path.stat().st_size
        except Exception:
            pass
        
        return stats