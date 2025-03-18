# -*- coding: utf-8 -*-
import logging
import base64
import json
import werkzeug
import requests
from odoo import http, _
from odoo.http import request

_logger = logging.getLogger(__name__)

class HrExpenseOCRController(http.Controller):
    """Controller for HR Expense OCR operations"""

    @http.route('/hr_expense/scan_receipt', type='json', auth='user')
    def scan_receipt(self, expense_id=None, attachment_id=None):
        """
        Process receipt scanning request
        
        Args:
            expense_id (int): ID of the expense record
            attachment_id (int): ID of the attachment to scan
            
        Returns:
            dict: Result of the scanning operation
        """
        # Security check
        if not expense_id or not attachment_id:
            _logger.warning("Missing required parameters for receipt scanning: expense_id=%s, attachment_id=%s", 
                          expense_id, attachment_id)
            return {'error': _('Missing required parameters')}
        
        try:
            # Get expense record
            expense = request.env['hr.expense'].browse(int(expense_id))
            if not expense.exists():
                _logger.warning("Expense record not found: %s", expense_id)
                return {'error': _('Expense record not found')}
            
            # Get attachment record
            attachment = request.env['ir.attachment'].browse(int(attachment_id))
            if not attachment.exists():
                _logger.warning("Attachment not found: %s", attachment_id)
                return {'error': _('Attachment not found')}
            
            # Check if attachment belongs to expense
            if attachment not in expense.attachment_ids:
                _logger.warning("Attachment %s does not belong to expense %s", 
                              attachment_id, expense_id)
                return {'error': _('Attachment does not belong to this expense')}
            
            # Check if expense is already scanned
            if expense.is_scanned:
                _logger.info("Expense %s is already scanned", expense_id)
                return {
                    'success': True,
                    'message': _('Receipt is already scanned')
                }
            
            # Update OCR status to processing
            expense.write({
                'ocr_status': 'processing'
            })
            
        except (ValueError, TypeError) as e:
            _logger.exception("Error validating parameters for receipt scanning: %s", str(e))
            return {'error': _('Invalid parameters')}
        
        try:
            # Get file data
            file_data = base64.b64decode(attachment.datas)
            file_name = attachment.name
            
            _logger.info("Processing receipt scan for expense %s with file %s", 
                       expense_id, file_name)
            
            # Import here to avoid circular imports
            from ..services.ocr_service import process_receipt_ocr
            
            # Process OCR
            ocr_result = process_receipt_ocr(file_data, file_name)
            
            if not ocr_result:
                _logger.error("OCR processing failed for expense %s", expense_id)
                return {
                    'success': False,
                    'error': _('OCR processing failed. Please check the logs for details.')
                }
            
            # Update expense with OCR data
            expense.write({
                'ocr_data': json.dumps(ocr_result),
                'ocr_status': 'done',
                'is_scanned': True
            })
            
            # Map OCR data to expense fields
            return self.map_ocr_data_to_expense(expense_id, ocr_result)
            
        except (ValueError, TypeError) as e:
            _logger.exception("Data error during OCR processing for expense %s: %s", 
                            expense_id, str(e))
            return {
                'success': False,
                'error': _('Data error during OCR processing: %s') % str(e)
            }
        except requests.exceptions.RequestException as e:
            _logger.exception("API request error during OCR processing for expense %s: %s", 
                            expense_id, str(e))
            return {
                'success': False,
                'error': _('Error connecting to OCR service: %s') % str(e)
            }
        except Exception as e:
            _logger.exception("Error during OCR processing for expense %s: %s", 
                            expense_id, str(e))
            return {
                'success': False,
                'error': _('An unexpected error occurred during OCR processing')
            }

    @http.route('/hr_expense/map_ocr_data', type='json', auth='user')
    def map_ocr_data_to_expense(self, expense_id=None, ocr_data=None):
        """
        Map OCR data to expense fields
        
        Args:
            expense_id (int): ID of the expense record
            ocr_data (dict): OCR data to map
            
        Returns:
            dict: Result of the mapping operation
        """
        # Security check
        if not expense_id or not ocr_data:
            _logger.warning("Missing required parameters for OCR data mapping: expense_id=%s", expense_id)
            return {'error': _('Missing required parameters')}
        
        try:
            # Get expense record
            expense = request.env['hr.expense'].browse(int(expense_id))
            if not expense.exists():
                _logger.warning("Expense record not found: %s", expense_id)
                return {'error': _('Expense record not found')}
            
            # Map OCR data to expense fields
            result = expense.map_ocr_data_to_expense(ocr_data)
            
            if not result:
                _logger.warning("Failed to map OCR data to expense %s", expense_id)
                return {
                    'success': False,
                    'message': _('No useful data found in OCR result')
                }
            
            return {
                'success': True,
                'message': _('OCR data mapped successfully')
            }
            
        except (ValueError, TypeError) as e:
            _logger.exception("Data error during OCR data mapping for expense %s: %s", 
                            expense_id, str(e))
            return {
                'success': False,
                'error': _('Data error during OCR data mapping: %s') % str(e)
            }
        except Exception as e:
            _logger.exception("Error during OCR data mapping for expense %s: %s", 
                            expense_id, str(e))
            return {
                'success': False,
                'error': _('An unexpected error occurred during OCR data mapping')
            }
