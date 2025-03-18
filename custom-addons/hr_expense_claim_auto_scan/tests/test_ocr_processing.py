# -*- coding: utf-8 -*-
import logging
from odoo.tests import common

_logger = logging.getLogger(__name__)

class TestOCRProcessing(common.TransactionCase):
    """Test OCR processing functionality"""

    def setUp(self):
        super(TestOCRProcessing, self).setUp()
        # Create a test expense record
        self.expense = self.env['hr.expense'].create({
            'name': 'Test Expense',
            'employee_id': self.env.ref('hr.employee_admin').id,
            'product_id': self.env.ref('hr_expense.product_product_fixed_cost').id,
            'total_amount': 100.0,
        })
        _logger.info("Created test expense record with ID: %s", self.expense.id)

    def test_ocr_result_processing(self):
        """Test processing OCR results with the new format"""
        # Sample OCR response
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

        _logger.info("Testing OCR processing with sample response")
        
        # Call the update method directly
        self.expense.update_from_ocr_result(sample_response)
        
        # Verify the results
        self.assertEqual(self.expense.business_name, 'Vibasel Outlets')
        self.assertEqual(self.expense.receipt_number, '8901')
        self.assertEqual(self.expense.total_amount, 400.58)
        self.assertEqual(self.expense.name, 'HNRY BPCK PBB LEATHE;OXB (+1 more items)')
        
        # Log the results
        _logger.info("Updated expense record:")
        _logger.info("- Name: %s", self.expense.name)
        _logger.info("- Business Name: %s", self.expense.business_name)
        _logger.info("- Receipt Number: %s", self.expense.receipt_number)
        _logger.info("- Total Amount: %s", self.expense.total_amount)
        _logger.info("- Date: %s", self.expense.date)

    def test_ocr_result_legacy_format(self):
        """Test processing OCR results with the legacy format"""
        # Sample OCR response in legacy format
        legacy_response = {
            'vendor': 'Legacy Vendor Inc.',
            'receipt_number': 'LR-12345',
            'date': '2023-01-15',
            'total': '299.99',
            'description': 'Office supplies'
        }

        _logger.info("Testing OCR processing with legacy response format")
        
        # Call the update method directly
        self.expense.update_from_ocr_result(legacy_response)
        
        # Verify the results
        self.assertEqual(self.expense.business_name, 'Legacy Vendor Inc.')
        self.assertEqual(self.expense.receipt_number, 'LR-12345')
        self.assertEqual(self.expense.total_amount, 299.99)
        self.assertEqual(self.expense.name, 'Office supplies')
        
        # Log the results
        _logger.info("Updated expense record with legacy format:")
        _logger.info("- Name: %s", self.expense.name)
        _logger.info("- Business Name: %s", self.expense.business_name)
        _logger.info("- Receipt Number: %s", self.expense.receipt_number)
        _logger.info("- Total Amount: %s", self.expense.total_amount)
        _logger.info("- Date: %s", self.expense.date)
