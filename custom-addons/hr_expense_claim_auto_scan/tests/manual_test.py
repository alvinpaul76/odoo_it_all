# -*- coding: utf-8 -*-
"""
Manual test script for OCR processing
Run this script from the Odoo shell when the database is available
"""
import logging
import base64

_logger = logging.getLogger(__name__)

def test_ocr_new_format(env):
    """Test the OCR processing with the new response format"""
    # Sample OCR response with the new format (output field)
    sample_response = {
        'output': {
            'business_name': 'Vibasel Outlets',
            'receipt_number': '8901',
            'date': '10/25/2017 10:36 PM',
            'items': [
                {
                    'quantity': 1,
                    'description': 'HNRY BPCK PBB LEATHE;OXB',
                    'amount': 261.75
                },
                {
                    'quantity': 1,
                    'description': 'WHRN CTSR PEB BELT;BLK/D',
                    'amount': 51.75
                }
            ],
            'subtotal': 375.5,
            'tax': 25.08,
            'total_amount': 400.58
        }
    }
    
    _logger.info("Testing OCR processing with new format response")
    
    # Get an expense record to test with
    expense = env['hr.expense'].search([], limit=1)
    if not expense:
        _logger.warning("No expense records found for testing")
        return
    
    _logger.info("Testing with expense ID: %s", expense.id)
    
    # Process the sample response
    expense.update_from_ocr_result(sample_response)
    
    # Log the results
    _logger.info("Updated expense record:")
    _logger.info("- Name: %s", expense.name)
    _logger.info("- Business Name: %s", expense.business_name)
    _logger.info("- Receipt Number: %s", expense.receipt_number)
    _logger.info("- Total Amount: %s", expense.total_amount)
    _logger.info("- Date: %s", expense.date)
    _logger.info("- OCR Status: %s", expense.ocr_status)
    
    return expense

def test_ocr_legacy_format(env):
    """Test the OCR processing with the legacy response format"""
    # Sample OCR response in legacy format
    legacy_response = {
        'vendor': 'Legacy Vendor Inc.',
        'receipt_number': 'LR-12345',
        'date': '2023-01-15',
        'total': '299.99',
        'description': 'Office supplies'
    }
    
    _logger.info("Testing OCR processing with legacy format response")
    
    # Get an expense record to test with
    expense = env['hr.expense'].search([], limit=1)
    if not expense:
        _logger.warning("No expense records found for testing")
        return
    
    _logger.info("Testing with expense ID: %s", expense.id)
    
    # Process the sample response
    expense.update_from_ocr_result(legacy_response)
    
    # Log the results
    _logger.info("Updated expense record:")
    _logger.info("- Name: %s", expense.name)
    _logger.info("- Business Name: %s", expense.business_name)
    _logger.info("- Receipt Number: %s", expense.receipt_number)
    _logger.info("- Total Amount: %s", expense.total_amount)
    _logger.info("- Date: %s", expense.date)
    _logger.info("- OCR Status: %s", expense.ocr_status)
    
    return expense

def test_ocr_service(env):
    """Test the OCR service with mock data"""
    from ..services.ocr_service import process_receipt_ocr
    
    # Create a simple PDF file for testing
    test_data = b'%PDF-1.4\n1 0 obj\n<</Type/Catalog/Pages 2 0 R>>\nendobj\n2 0 obj\n<</Type/Pages/Count 1/Kids[3 0 R]>>\nendobj\n3 0 obj\n<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R/Resources<<>>>>\nendobj\nxref\n0 4\n0000000000 65535 f\n0000000010 00000 n\n0000000053 00000 n\n0000000102 00000 n\ntrailer\n<</Size 4/Root 1 0 R>>\nstartxref\n178\n%%EOF\n'
    
    # Enable test mode for OCR service
    param = env['ir.config_parameter'].sudo()
    param.set_param('ocr_test_mode', 'True')
    
    _logger.info("Testing OCR service with mock data")
    
    # Process the test data
    result = process_receipt_ocr(test_data, 'test.pdf')
    
    # Log the result
    _logger.info("OCR service result: %s", result)
    
    # Disable test mode
    param.set_param('ocr_test_mode', 'False')
    
    return result

# When running in Odoo shell, you can call these functions directly:
# env = self.env  # In Odoo shell
# test_ocr_new_format(env)
# test_ocr_legacy_format(env)
# test_ocr_service(env)
