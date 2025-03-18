# -*- coding: utf-8 -*-
import base64
import logging
from datetime import datetime
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

from ..services.ocr_service import process_receipt_ocr

_logger = logging.getLogger(__name__)

class HrExpense(models.Model):
    _inherit = 'hr.expense'
    
    ocr_status = fields.Selection([
        ('pending', 'Pending'),
        ('processed', 'Processed'),
        ('failed', 'Failed')
    ], string='OCR Status', default=False, copy=False, help="Status of OCR processing for this expense")
    
    ocr_message = fields.Text(string='OCR Message', copy=False, size=256, help="Message from OCR processing")
    
    business_name = fields.Char(string='Business Name', copy=False, size=64, help="Business name extracted from receipt")
    
    receipt_number = fields.Char(string='Receipt Number', copy=False, size=32, help="Receipt number extracted from receipt")
    
    # Override abstract method from BaseModel to avoid lint error
    def onchange(self, values, field_name, field_onchange):
        return super(HrExpense, self).onchange(values, field_name, field_onchange)
    
    def auto_scan_attachment(self, attachment=None):
        """Process an attachment with OCR to extract expense data.
        
        Args:
            attachment: The attachment to process. If not provided, uses the main attachment.
            
        Returns:
            bool: True if processing was successful, False otherwise.
        """
        self.ensure_one()
        
        if not attachment:
            # Get the main attachment if none provided
            if hasattr(self, 'message_main_attachment_id') and self.message_main_attachment_id:
                attachment = self.message_main_attachment_id
            
        if not attachment:
            _logger.info("No attachment found for expense %s", self.id)
            self.write({
                'ocr_status': 'failed',
                'ocr_message': _("No receipt attachment found to scan.")
            })
            return False
            
        try:
            _logger.info("Processing attachment %s for expense %s", attachment.id, self.id)
            
            # Update status to processing
            self.write({'ocr_status': 'pending'})
            
            # Get file data and name
            file_data = base64.b64decode(attachment.datas)
            file_name = attachment.name or 'unknown'
            
            # Process the receipt with OCR
            ocr_result = process_receipt_ocr(file_data, file_name)
            
            if not ocr_result:
                _logger.warning("OCR processing returned no result for expense %s", self.id)
                self.write({
                    'ocr_status': 'failed',
                    'ocr_message': _("OCR processing failed to extract data from the receipt.")
                })
                return False
                
            # Update expense with OCR result
            self.update_from_ocr_result(ocr_result)
            return True
            
        except UserError as e:
            _logger.error("User error in OCR processing for expense %s: %s", self.id, str(e))
            self.write({
                'ocr_status': 'failed',
                'ocr_message': str(e)
            })
            return False
        except (ValueError, TypeError, ValidationError) as e:
            _logger.error("Validation error in OCR processing for expense %s: %s", self.id, str(e))
            self.write({
                'ocr_status': 'failed',
                'ocr_message': _("Validation error during OCR processing: %s") % str(e)[:200]
            })
            return False
        except Exception as e:
            _logger.error("Error in OCR processing for expense %s: %s", self.id, str(e), exc_info=True)
            self.write({
                'ocr_status': 'failed',
                'ocr_message': _("An error occurred during OCR processing: %s") % str(e)[:200]
            })
            return False
    
    @api.model_create_multi
    def create(self, vals_list):
        """Override create to trigger OCR processing on creation if attachment exists."""
        expenses = super(HrExpense, self).create(vals_list)
        
        for expense in expenses:
            # Check if there's an attachment and auto-scan it
            if hasattr(expense, 'message_main_attachment_id') and expense.message_main_attachment_id:
                _logger.info("New expense %s created with attachment, triggering OCR scan", expense.id)
                expense.auto_scan_attachment(expense.message_main_attachment_id)
            
        return expenses
    
    def write(self, vals):
        """Override write to trigger OCR processing when main attachment changes."""
        result = super(HrExpense, self).write(vals)
        
        # If the main attachment was updated, process it with OCR
        if 'message_main_attachment_id' in vals:
            for expense in self:
                if hasattr(expense, 'message_main_attachment_id') and expense.message_main_attachment_id:
                    _logger.info("Main attachment updated for expense %s, triggering OCR scan", expense.id)
                    expense.auto_scan_attachment(expense.message_main_attachment_id)
        
        return result
    
    def update_from_ocr_result(self, ocr_data):
        """
        Update expense fields from OCR result data.
        
        Args:
            ocr_data (dict): Dictionary containing OCR extracted data
        
        Returns:
            bool: True if successful
        """
        self.ensure_one()
        
        _logger.info("Updating expense %s with OCR result: %s", self.id, ocr_data)
        
        # Check if OCR data contains an error
        if ocr_data and 'error' in ocr_data:
            error_message = ocr_data.get('error')
            _logger.error("OCR processing failed for expense %s: %s", self.id, error_message)
            self.write({
                'ocr_status': 'failed',
                'ocr_message': _("OCR processing failed to extract data from the receipt. %s") % error_message[:256]
            })
            return False
        
        # Check if we have the new format (with 'output' field)
        if isinstance(ocr_data, dict) and 'output' in ocr_data:
            _logger.info("Processing new OCR format with 'output' field for expense %s", self.id)
            ocr_data = ocr_data.get('output', {})
        
        if not ocr_data or not isinstance(ocr_data, dict):
            _logger.warning("Invalid OCR data format for expense %s", self.id)
            self.write({
                'ocr_status': 'failed',
                'ocr_message': _("Invalid OCR data format received.")[:256]
            })
            return False
            
        vals = {}
        
        # Extract business name
        if ocr_data.get('business_name'):
            vals['business_name'] = ocr_data.get('business_name')[:64]
        elif ocr_data.get('vendor'):
            vals['business_name'] = ocr_data.get('vendor')[:64]
            
        # Extract receipt number
        if ocr_data.get('receipt_number'):
            vals['receipt_number'] = ocr_data.get('receipt_number')[:32]
            
        # Extract total amount
        total_amount = None
        if ocr_data.get('total_amount'):
            total_amount = ocr_data.get('total_amount')
        elif ocr_data.get('total'):
            total_amount = ocr_data.get('total')
            
        if total_amount:
            # Convert to float if it's a string
            if isinstance(total_amount, str):
                try:
                    total_amount = float(total_amount.replace(',', ''))
                except (ValueError, TypeError):
                    _logger.warning("Could not convert total amount '%s' to float for expense %s", 
                                   total_amount, self.id)
            vals['total_amount_currency'] = total_amount
            
        # Extract tax amount
        tax_amount = None
        if ocr_data.get('tax_amount'):
            tax_amount = ocr_data.get('tax_amount')
        elif ocr_data.get('tax'):
            tax_amount = ocr_data.get('tax')
            
        if tax_amount:
            # Convert to float if it's a string
            if isinstance(tax_amount, str):
                try:
                    tax_amount = float(tax_amount.replace(',', ''))
                    _logger.info("Extracted tax amount %s for expense %s", tax_amount, self.id)
                except (ValueError, TypeError):
                    _logger.warning("Could not convert tax amount '%s' to float for expense %s", 
                                   tax_amount, self.id)
            
            # Update the tax_amount_currency field with the extracted tax amount
            vals['tax_amount_currency'] = tax_amount
            _logger.info("Updated tax_amount_currency to %s for expense %s", tax_amount, self.id)
        
        # Extract date
        expense_date = None
        if ocr_data.get('date'):
            date_str = ocr_data.get('date')
            try:
                # Try different date formats
                for fmt in ['%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y', '%m/%d/%Y %I:%M %p', '%d/%m/%Y %H:%M']:
                    try:
                        expense_date = datetime.strptime(date_str, fmt).date()
                        break
                    except ValueError:
                        continue
                    
                if expense_date:
                    vals['date'] = expense_date
            except (ValueError, TypeError) as e:
                _logger.warning("Could not parse date '%s' for expense %s: %s", 
                               date_str, self.id, str(e))
                
        # Extract description from line items if available
        if ocr_data.get('items') and isinstance(ocr_data.get('items'), list):
            items = ocr_data.get('items')
            _logger.info("Found %d line items in OCR result for expense %s", len(items), self.id)
            
            # Use the first item description as the expense name if not set
            if items and self.env['hr.expense']._fields.get('name') and hasattr(self, 'name') and not self.name:
                first_item = items[0]
                if first_item.get('description'):
                    vals['name'] = first_item.get('description')
        elif ocr_data.get('description') and self.env['hr.expense']._fields.get('name') and hasattr(self, 'name') and not self.name:
            vals['name'] = ocr_data.get('description')
            
        # Update expense with extracted values
        if vals:
            vals['ocr_status'] = 'processed'
            vals['ocr_message'] = _("Receipt data successfully extracted.")[:256]
            self.write(vals)
            _logger.info("Updated expense %s with OCR data: %s", self.id, vals)
        else:
            self.write({
                'ocr_status': 'processed',
                'ocr_message': _("Receipt processed but no useful data was extracted.")[:256]
            })
            _logger.warning("No useful data extracted from OCR for expense %s", self.id)
            
        return True
    
    def action_scan_receipt(self):
        """Manual action to scan receipt attachment."""
        self.ensure_one()
        
        # Check for attachment using safer method
        has_attachment = False
        if self.env['hr.expense']._fields.get('message_main_attachment_id'):
            if hasattr(self, 'message_main_attachment_id') and self.message_main_attachment_id:
                has_attachment = True
        
        if not has_attachment:
            raise UserError(_("No receipt attachment found. Please attach a receipt first."))
            
        try:
            result = self.auto_scan_attachment(self.message_main_attachment_id)
            if result:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _("Receipt Scanned"),
                        'message': _("Receipt successfully scanned and data extracted."),
                        'sticky': False,
                        'type': 'success',
                    }
                }
            else:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _("Scan Failed"),
                        'message': self.ocr_message or _("Failed to extract data from receipt."),
                        'sticky': True,
                        'type': 'warning',
                    }
                }
        except UserError as e:
            _logger.error("User error in manual receipt scanning for expense %s: %s", self.id, str(e))
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _("Scan Error"),
                    'message': str(e),
                    'sticky': True,
                    'type': 'danger',
                }
            }
        except (ValueError, TypeError, ValidationError) as e:
            _logger.error("Validation error in manual receipt scanning for expense %s: %s", self.id, str(e))
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _("Scan Error"),
                    'message': str(e),
                    'sticky': True,
                    'type': 'danger',
                }
            }
        except Exception as e:
            _logger.error("Error in manual receipt scanning for expense %s: %s", self.id, str(e), exc_info=True)
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _("Scan Error"),
                    'message': str(e),
                    'sticky': True,
                    'type': 'danger',
                }
            }
