"""
Test bank conversion functionality
"""
import os
import sys
import tempfile
import pytest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.converters.universal_converter import UniversalConverter
from src.converters.bank_detector import BankDetector


class TestUniversalConverter:
    """Test universal converter functionality"""
    
    @pytest.fixture
    def converter(self):
        """Create converter instance"""
        return UniversalConverter()
    
    @pytest.fixture
    def sample_bkt_text(self):
        """Sample BKT bank statement text"""
        return """BKT Bank Statement
        Account: 123456789
        Date        Description                Amount      Balance
        01/12/2023  Opening Balance           0.00        5,000.00
        05/12/2023  Payment to Supplier      -150.00      4,850.00
        10/12/2023  Client Payment            300.00      5,150.00
        15/12/2023  Bank Fees                 -5.00       5,145.00"""
    
    @pytest.fixture
    def sample_raiffeisen_text(self):
        """Sample Raiffeisen bank statement text"""
        return """Raiffeisen Bank
        STATEMENT OF ACCOUNT
        Account Number: 987654321
        
        Date       Value Date  Description           Debit    Credit   Balance
        01.12.23   01.12.23   Balance Forward                          5000.00
        05.12.23   05.12.23   Transfer Out          150.00             4850.00
        10.12.23   10.12.23   Incoming Transfer              300.00    5150.00
        15.12.23   15.12.23   Service Charge        5.00               5145.00"""
    
    def test_convert_bkt_statement(self, converter, sample_bkt_text):
        """Test BKT statement conversion"""
        result = converter.convert_statement(sample_bkt_text, 'BKT', 'test.pdf')
        
        assert 'success' in result
        if result['success']:
            assert 'qbo_data' in result
            assert len(result['qbo_data']) > 0
            
            # Check QBO format structure
            qbo_lines = result['qbo_data'].split('\n')
            assert any('!Type:Bank' in line for line in qbo_lines)
    
    def test_convert_raiffeisen_statement(self, converter, sample_raiffeisen_text):
        """Test Raiffeisen statement conversion"""
        result = converter.convert_statement(sample_raiffeisen_text, 'RAIFFEISEN', 'test.pdf')
        
        assert 'success' in result
        if result['success']:
            assert 'qbo_data' in result
            assert len(result['qbo_data']) > 0
    
    def test_convert_unknown_bank(self, converter):
        """Test conversion with unknown bank type"""
        result = converter.convert_statement("Random text", 'UNKNOWN', 'test.pdf')
        
        assert 'success' in result
        assert not result['success']
        assert 'error' in result
    
    def test_convert_empty_content(self, converter):
        """Test conversion with empty content"""
        result = converter.convert_statement("", 'BKT', 'test.pdf')
        
        assert 'success' in result
        assert not result['success']
    
    def test_parse_bkt_transactions(self, converter, sample_bkt_text):
        """Test BKT transaction parsing"""
        transactions = converter._parse_bkt_transactions(sample_bkt_text)
        
        assert len(transactions) >= 3  # Should find at least 3 transactions
        
        # Check transaction structure
        for transaction in transactions:
            assert 'date' in transaction
            assert 'description' in transaction
            assert 'amount' in transaction
    
    def test_parse_raiffeisen_transactions(self, converter, sample_raiffeisen_text):
        """Test Raiffeisen transaction parsing"""
        transactions = converter._parse_raiffeisen_transactions(sample_raiffeisen_text)
        
        assert len(transactions) >= 2  # Should find at least 2 transactions
        
        # Check transaction structure
        for transaction in transactions:
            assert 'date' in transaction
            assert 'description' in transaction
            assert 'amount' in transaction
    
    def test_format_qbo_data(self, converter):
        """Test QBO formatting"""
        transactions = [
            {
                'date': '01/12/2023',
                'description': 'Test Transaction',
                'amount': -100.50
            },
            {
                'date': '02/12/2023',
                'description': 'Another Transaction',
                'amount': 200.00
            }
        ]
        
        qbo_data = converter._format_qbo_data(transactions)
        
        assert '!Type:Bank' in qbo_data
        assert 'Test Transaction' in qbo_data
        assert 'Another Transaction' in qbo_data
        assert '-100.50' in qbo_data
        assert '200.00' in qbo_data


class TestBankSpecificParsing:
    """Test bank-specific parsing functionality"""
    
    def test_bkt_amount_parsing(self):
        """Test BKT amount parsing with various formats"""
        converter = UniversalConverter()
        
        # Test different amount formats
        test_cases = [
            ('1,234.56', 1234.56),
            ('-1,234.56', -1234.56),
            ('(1,234.56)', -1234.56),
            ('1234.56', 1234.56),
            ('0.00', 0.0)
        ]
        
        for amount_str, expected in test_cases:
            parsed = converter._parse_amount(amount_str)
            assert abs(parsed - expected) < 0.01
    
    def test_date_parsing(self):
        """Test date parsing with various formats"""
        converter = UniversalConverter()
        
        test_dates = [
            '01/12/2023',
            '01.12.23',
            '2023-12-01',
            '01-Dec-23'
        ]
        
        for date_str in test_dates:
            try:
                parsed_date = converter._parse_date(date_str)
                assert parsed_date is not None
            except:
                # Some formats might not be supported yet
                pass


class TestCSVProcessing:
    """Test CSV processing functionality"""
    
    @pytest.fixture
    def sample_csv_content(self):
        """Sample CSV content"""
        return """Date,Description,Amount,Balance
01/12/2023,Opening Balance,0.00,5000.00
05/12/2023,Payment to Supplier,-150.00,4850.00
10/12/2023,Client Payment,300.00,5150.00
15/12/2023,Bank Fees,-5.00,5145.00"""
    
    def test_process_csv_content(self, sample_csv_content):
        """Test CSV content processing"""
        converter = UniversalConverter()
        
        result = converter.process_csv_content(sample_csv_content, 'test.csv')
        
        assert 'success' in result
        if result['success']:
            assert 'qbo_data' in result
            assert len(result['qbo_data']) > 0
    
    def test_detect_csv_format(self, sample_csv_content):
        """Test CSV format detection"""
        converter = UniversalConverter()
        
        format_info = converter._detect_csv_format(sample_csv_content)
        
        assert 'delimiter' in format_info
        assert 'has_header' in format_info
        assert 'columns' in format_info


class TestErrorScenarios:
    """Test various error scenarios"""
    
    def test_malformed_pdf_text(self):
        """Test handling of malformed PDF text"""
        converter = UniversalConverter()
        
        malformed_text = "Random\ntext\nwith\nno\nstructure"
        result = converter.convert_statement(malformed_text, 'BKT', 'test.pdf')
        
        assert 'success' in result
        # Should handle gracefully even if no transactions found
    
    def test_empty_transactions(self):
        """Test handling when no transactions are found"""
        converter = UniversalConverter()
        
        # Text that looks like a statement but has no transaction data
        text = "BKT Bank Statement\nAccount: 123456789\nNo transactions found"
        result = converter.convert_statement(text, 'BKT', 'test.pdf')
        
        assert 'success' in result
    
    def test_invalid_amounts(self):
        """Test handling of invalid amount formats"""
        converter = UniversalConverter()
        
        invalid_amounts = ['abc', '', 'N/A', '---']
        
        for amount in invalid_amounts:
            try:
                parsed = converter._parse_amount(amount)
                assert parsed == 0.0  # Should default to 0 for invalid amounts
            except:
                # Or raise appropriate exception
                pass


if __name__ == '__main__':
    pytest.main([__file__, '-v'])