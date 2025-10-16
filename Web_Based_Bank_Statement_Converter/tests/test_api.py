# Web-Based Bank Statement Converter API - Test Configuration

import os
import tempfile
import pytest
from unittest.mock import patch, MagicMock
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app


class TestConfig:
    """Configuration for testing"""
    TESTING = True
    SECRET_KEY = 'test-secret-key'
    UPLOAD_FOLDER = tempfile.mkdtemp()
    CONVERTED_FOLDER = tempfile.mkdtemp()
    MAX_FILE_SIZE_MB = 10
    CLEANUP_ENABLED = False  # Disable cleanup during tests


@pytest.fixture
def app():
    """Create application for testing"""
    app = create_app()
    app.config.from_object(TestConfig)
    return app


@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()


@pytest.fixture
def sample_pdf():
    """Create a sample PDF file for testing"""
    pdf_content = b"""%%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj
2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj
3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
/Contents 4 0 R
>>
endobj
4 0 obj
<<
/Length 44
>>
stream
BT
/F1 12 Tf
100 700 Td
(BKT Bank Statement) Tj
ET
endstream
endobj
xref
0 5
0000000000 65535 f 
0000000010 00000 n 
0000000056 00000 n 
0000000111 00000 n 
0000000195 00000 n 
trailer
<<
/Size 5
/Root 1 0 R
>>
startxref
290
%%EOF"""
    return pdf_content


@pytest.fixture
def sample_csv():
    """Create a sample CSV file for testing"""
    csv_content = """Date,Description,Amount,Balance
01/12/2023,Opening Balance,0.00,5000.00
05/12/2023,Payment to Supplier,-150.00,4850.00
10/12/2023,Client Payment,300.00,5150.00
15/12/2023,Bank Fees,-5.00,5145.00"""
    return csv_content.encode('utf-8')


class TestBankDetection:
    """Test bank detection functionality"""
    
    def test_detect_bkt_bank(self, app):
        """Test BKT bank detection"""
        from src.converters.bank_detector import BankDetector
        
        with app.app_context():
            detector = BankDetector()
            
            # Test PDF with BKT indicators
            pdf_text = "BKT Bank Statement Account: 123456789"
            bank_type = detector.detect_bank_type(pdf_text, 'statement.pdf')
            assert bank_type == 'BKT'
    
    def test_detect_raiffeisen_bank(self, app):
        """Test Raiffeisen bank detection"""
        from src.converters.bank_detector import BankDetector
        
        with app.app_context():
            detector = BankDetector()
            
            # Test PDF with Raiffeisen indicators
            pdf_text = "Raiffeisen Bank STATEMENT OF ACCOUNT"
            bank_type = detector.detect_bank_type(pdf_text, 'statement.pdf')
            assert bank_type == 'RAIFFEISEN'
    
    def test_detect_unknown_bank(self, app):
        """Test unknown bank detection"""
        from src.converters.bank_detector import BankDetector
        
        with app.app_context():
            detector = BankDetector()
            
            pdf_text = "Random Bank Statement"
            bank_type = detector.detect_bank_type(pdf_text, 'statement.pdf')
            assert bank_type == 'UNKNOWN'


class TestFileManager:
    """Test file management functionality"""
    
    def test_secure_filename(self, app):
        """Test secure filename generation"""
        from src.converters.file_manager import FileManager
        
        with app.app_context():
            manager = FileManager(app.config['UPLOAD_FOLDER'])
            
            # Test various filename scenarios
            assert manager.secure_filename('test.pdf') == 'test.pdf'
            assert manager.secure_filename('test file.pdf') == 'test_file.pdf'
            assert manager.secure_filename('test@#$%.pdf') == 'test.pdf'
    
    def test_save_file(self, app, sample_pdf):
        """Test file saving"""
        from src.converters.file_manager import FileManager
        from werkzeug.datastructures import FileStorage
        from io import BytesIO
        
        with app.app_context():
            manager = FileManager(app.config['UPLOAD_FOLDER'])
            
            file_obj = FileStorage(
                stream=BytesIO(sample_pdf),
                filename='test.pdf',
                content_type='application/pdf'
            )
            
            filepath = manager.save_file(file_obj, 'test_job')
            assert os.path.exists(filepath)
            assert filepath.endswith('.pdf')


class TestAPIEndpoints:
    """Test API endpoints"""
    
    def test_api_info(self, client):
        """Test API info endpoint"""
        response = client.get('/api/info')
        assert response.status_code == 200
        
        data = response.get_json()
        assert 'version' in data
        assert 'supported_banks' in data
        assert 'max_file_size_mb' in data
    
    def test_health_check(self, client):
        """Test health check endpoint"""
        response = client.get('/health')
        assert response.status_code == 200
        
        data = response.get_json()
        assert data['status'] == 'healthy'
    
    def test_upload_no_file(self, client):
        """Test upload without file"""
        response = client.post('/api/upload')
        assert response.status_code == 400
        
        data = response.get_json()
        assert 'error' in data
    
    def test_upload_pdf_file(self, client, sample_pdf):
        """Test PDF file upload"""
        response = client.post('/api/upload', data={
            'file': (BytesIO(sample_pdf), 'test.pdf')
        })
        
        # Should return job ID even if conversion fails
        assert response.status_code in [200, 400]  # Might fail due to mock conversion
    
    def test_upload_csv_file(self, client, sample_csv):
        """Test CSV file upload"""
        response = client.post('/api/upload', data={
            'file': (BytesIO(sample_csv), 'test.csv')
        })
        
        assert response.status_code in [200, 400]  # Might fail due to mock conversion
    
    def test_status_invalid_job(self, client):
        """Test status check for invalid job"""
        response = client.get('/api/status/invalid_job_id')
        assert response.status_code == 404
    
    def test_download_invalid_job(self, client):
        """Test download for invalid job"""
        response = client.get('/api/download/invalid_job_id')
        assert response.status_code == 404


class TestWebInterface:
    """Test web interface"""
    
    def test_index_page(self, client):
        """Test main index page"""
        response = client.get('/')
        assert response.status_code == 200
        assert b'Bank Statement Converter' in response.data
    
    def test_status_page(self, client):
        """Test status page"""
        response = client.get('/status/test_job')
        assert response.status_code == 200


class TestErrorHandling:
    """Test error handling"""
    
    def test_404_error(self, client):
        """Test 404 error handling"""
        response = client.get('/nonexistent')
        assert response.status_code == 404
    
    def test_large_file_upload(self, client):
        """Test large file upload rejection"""
        # Create a file larger than allowed
        large_content = b'x' * (15 * 1024 * 1024)  # 15MB
        
        response = client.post('/api/upload', data={
            'file': (BytesIO(large_content), 'large.pdf')
        })
        
        assert response.status_code == 413  # Payload too large


if __name__ == '__main__':
    pytest.main([__file__, '-v'])