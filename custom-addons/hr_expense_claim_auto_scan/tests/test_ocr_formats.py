# -*- coding: utf-8 -*-
"""
Test script for OCR response format handling
This test verifies that the HR Expense module correctly handles both
new and legacy OCR response formats
"""
import base64
import logging
from odoo.tests import common, tagged

_logger = logging.getLogger(__name__)

@tagged('post_install', '-at_install')
class TestOCRFormats(common.TransactionCase):
    """Test class for OCR response format handling"""

    def setUp(self):
        super(TestOCRFormats, self).setUp()
        # Create a test expense
        self.expense = self.env['hr.expense'].create({
            'name': 'Test Expense',
            'employee_id': self.env.ref('hr.employee_admin').id,
            'product_id': self.env.ref('hr_expense.product_product_fixed_cost').id,
            'total_amount': 100.0,
        })
        _logger.info("Created test expense with ID: %s", self.expense.id)
        
        # Enable test mode for OCR service
        self.env['ir.config_parameter'].sudo().set_param('ocr_test_mode', 'True')
        
        # Create a simple PDF attachment
        pdf_data = b'%PDF-1.4\n1 0 obj\n<</Type/Catalog/Pages 2 0 R>>\nendobj\n2 0 obj\n<</Type/Pages/Count 1/Kids[3 0 R]>>\nendobj\n3 0 obj\n<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R/Resources<<>>>>\nendobj\nxref\n0 4\n0000000000 65535 f\n0000000010 00000 n\n0000000053 00000 n\n0000000102 00000 n\ntrailer\n<</Size 4/Root 1 0 R>>\nstartxref\n178\n%%EOF\n'
        self.attachment = self.env['ir.attachment'].create({
            'name': 'test_receipt.pdf',
            'datas': base64.b64encode(pdf_data),
            'res_model': 'hr.expense',
            'res_id': self.expense.id,
        })
        _logger.info("Created test attachment with ID: %s", self.attachment.id)
        
        # Link the attachment to the expense
        self.expense.message_main_attachment_id = self.attachment.id

    def test_01_new_format_handling(self):
        """Test handling of the new OCR response format with nested 'output' field"""
        _logger.info("Testing new OCR response format handling")
        
        # Sample OCR response with the new format
        new_format_response = {
            'output': {
                'business_name': 'Test Company Inc.',
                'receipt_number': 'INV-12345',
                'date': '2023-05-15',
                'items': [
                    {
                        'quantity': 1,
                        'description': 'Office Supplies',
                        'amount': 75.50
                    },
                    {
                        'quantity': 2,
                        'description': 'Printer Paper',
                        'amount': 24.50
                    }
                ],
                'subtotal': 100.0,
                'tax': 10.0,
                'total_amount': 110.0
            }
        }
        
        # Update expense with the OCR result
        self.expense.update_from_ocr_result(new_format_response)
        
        # Verify the expense was updated correctly
        self.assertEqual(self.expense.business_name, 'Test Company Inc.', 
                         "Business name not correctly extracted from new format")
        self.assertEqual(self.expense.receipt_number, 'INV-12345', 
                         "Receipt number not correctly extracted from new format")
        self.assertEqual(self.expense.total_amount, 110.0, 
                         "Total amount not correctly extracted from new format")
        self.assertEqual(self.expense.ocr_status, 'processed', 
                         "OCR status not correctly set after processing new format")
        
        _logger.info("New format test passed successfully")

    def test_02_legacy_format_handling(self):
        """Test handling of the legacy OCR response format (flat structure)"""
        _logger.info("Testing legacy OCR response format handling")
        
        # Reset the expense
        self.expense.write({
            'business_name': False,
            'receipt_number': False,
            'total_amount': 100.0,
            'ocr_status': False,
            'ocr_message': False,
        })
        
        # Sample OCR response with the legacy format
        legacy_format_response = {
            'vendor': 'Legacy Vendor LLC',
            'receipt_number': 'REC-9876',
            'date': '2023-06-20',
            'total': '250.75',
            'description': 'Office Equipment'
        }
        
        # Update expense with the OCR result
        self.expense.update_from_ocr_result(legacy_format_response)
        
        # Verify the expense was updated correctly
        self.assertEqual(self.expense.business_name, 'Legacy Vendor LLC', 
                         "Business name not correctly extracted from legacy format")
        self.assertEqual(self.expense.receipt_number, 'REC-9876', 
                         "Receipt number not correctly extracted from legacy format")
        self.assertEqual(self.expense.total_amount, 250.75, 
                         "Total amount not correctly extracted from legacy format")
        self.assertEqual(self.expense.name, 'Office Equipment', 
                         "Description not correctly extracted from legacy format")
        self.assertEqual(self.expense.ocr_status, 'processed', 
                         "OCR status not correctly set after processing legacy format")
        
        _logger.info("Legacy format test passed successfully")

    def test_03_auto_scan_attachment(self):
        """Test automatic scanning of attachments"""
        _logger.info("Testing automatic scanning of attachments")
        
        # Reset the expense
        self.expense.write({
            'business_name': False,
            'receipt_number': False,
            'total_amount': 100.0,
            'ocr_status': False,
            'ocr_message': False,
        })
        
        # Trigger the auto scan
        result = self.expense.auto_scan_attachment(self.attachment)
        
        # Verify the scan was successful
        self.assertTrue(result, "Auto scan attachment should return True on success")
        self.assertEqual(self.expense.ocr_status, 'processed', 
                         "OCR status should be 'processed' after successful scan")
        
        _logger.info("Auto scan attachment test passed successfully")

    def tearDown(self):
        # Disable test mode
        self.env['ir.config_parameter'].sudo().set_param('ocr_test_mode', 'False')
        super(TestOCRFormats, self).tearDown()
