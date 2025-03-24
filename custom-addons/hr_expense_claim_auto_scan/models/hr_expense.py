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
    
    ocr_message = fields.Text(string='OCR Message', copy=False, size=2048, help="Message from OCR processing")
    
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
                'ocr_message': _("No receipt attachment found to scan.")[:2048]
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
                    'ocr_message': _("OCR processing failed to extract data from the receipt.")[:2048]
                })
                return False
                
            # Update expense with OCR result
            self.update_from_ocr_result(ocr_result)
            return True
            
        except UserError as e:
            _logger.error("User error in OCR processing for expense %s: %s", self.id, str(e))
            self.write({
                'ocr_status': 'failed',
                'ocr_message': str(e)[:2048]
            })
            return False
        except (ValueError, TypeError, ValidationError) as e:
            _logger.error("Validation error in OCR processing for expense %s: %s", self.id, str(e))
            self.write({
                'ocr_status': 'failed',
                'ocr_message': _("Validation error during OCR processing: %s") % str(e)[:2048]
            })
            return False
        except Exception as e:
            _logger.error("Error in OCR processing for expense %s: %s", self.id, str(e), exc_info=True)
            self.write({
                'ocr_status': 'failed',
                'ocr_message': _("An error occurred during OCR processing: %s") % str(e)[:2048]
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
                'ocr_message': _("OCR processing failed to extract data from the receipt. %s") % error_message[:2048]
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
                'ocr_message': _("Invalid OCR data format received.")[:2048]
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
            _logger.info("Attempting to parse date from OCR data: %s", date_str)
            try:
                # Try different date formats
                for fmt in ['%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y', '%m-%d-%Y', '%d-%m-%Y', 
                           '%m/%d/%Y %I:%M %p', '%d/%m/%Y %H:%M', '%Y-%m-%dT%H:%M:%S',
                           '%B %d, %Y', '%d %B %Y']:
                    try:
                        expense_date = datetime.strptime(date_str, fmt).date()
                        _logger.info("Successfully parsed date '%s' with format '%s'", date_str, fmt)
                        break
                    except ValueError:
                        continue
                    
                if expense_date:
                    vals['date'] = expense_date
                    _logger.info("Set expense date to %s", expense_date)
                else:
                    _logger.warning("Could not parse date '%s' with any known format", date_str)
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
        
        # Set description based on receipt_description if available
        if ocr_data.get('receipt_description'):
            vals['name'] = ocr_data.get('receipt_description')
            _logger.info("Setting expense description from receipt_description: %s", ocr_data.get('receipt_description'))
        
        # Set expense category based on receipt_category if available
        if ocr_data.get('receipt_category') and self.env['hr.expense']._fields.get('product_id'):
            category_name = ocr_data.get('receipt_category')
            _logger.info("Looking for expense category matching: %s", category_name)
            
            # Get available expense categories
            available_products = self.env['product.product'].search([
                ('can_be_expensed', '=', True)
            ])
            
            if not available_products:
                _logger.warning("No expense categories (expensable products) found in the system")
            
            # Normalize the category name for better matching
            normalized_category = category_name
            if isinstance(normalized_category, str):
                normalized_category = normalized_category.strip().upper()
            
            # Try to find a matching product using multiple methods
            methods = [
                # Method 1: Exact match on default_code
                lambda: self.env['product.product'].search([
                    ('default_code', '=', category_name),
                    ('can_be_expensed', '=', True)
                ], limit=1),
                
                # Method 2: Case-insensitive match on default_code
                lambda: self.env['product.product'].search([
                    ('default_code', 'ilike', category_name),
                    ('can_be_expensed', '=', True)
                ], limit=1),
                
                # Method 3: Match on name
                lambda: self.env['product.product'].search([
                    ('name', 'ilike', category_name),
                    ('can_be_expensed', '=', True)
                ], limit=1),
                
                # Method 4: Manual comparison with normalized values
                lambda: self._find_product_by_normalized_code(available_products, normalized_category)
            ]
            
            # Try each method in sequence
            product = None
            for method in methods:
                product = method()
                if product:
                    break
            
            if product:
                vals['product_id'] = product.id
                _logger.info("Set expense category to product: %s (ID: %s)", product.name, product.id)
                
                # Add a note in the chatter about the OCR processing
                if hasattr(self, 'message_post'):
                    note = _("OCR Processing: Expense category set to '%s' based on receipt category '%s'.") % (
                        product.name, category_name)
                    self.message_post(body=note)
            else:
                _logger.info("No matching expense category found for: '%s'", category_name)
            
        # If no description was set from OCR data, use the filename of the attachment
        if not vals.get('name') and hasattr(self, 'message_main_attachment_id') and self.message_main_attachment_id:
            filename = self.message_main_attachment_id.name
            if filename:
                vals['name'] = filename
                _logger.info("Setting expense description to attachment filename: %s", filename)
            
        # Update expense with extracted values
        if vals:
            # Create a detailed OCR message with better formatting
            ocr_message_parts = [_("✅ Receipt data successfully extracted")]
            
            # Format the extracted data in a more visually appealing way
            details = []
            if 'business_name' in vals:
                details.append("🏢 %s: %s" % (_("Vendor"), vals['business_name']))
            if 'name' in vals:
                details.append("📝 %s: %s" % (_("Description"), vals['name']))
            if 'product_id' in vals:
                product = self.env['product.product'].browse(vals['product_id'])
                details.append("🏷️ %s: %s" % (_("Category"), product.name))
            if 'total_amount_currency' in vals:
                details.append("💰 %s: %s %s" % (
                    _("Amount"), 
                    vals['total_amount_currency'], 
                    self.currency_id.name if hasattr(self, 'currency_id') else ''))
            if 'date' in vals:
                details.append("📅 %s: %s" % (_("Date"), vals['date']))
            
            # Add the formatted details to the message
            if details:
                ocr_message_parts.append("\n".join(details))
            
            # Add itemized details if available
            if ocr_data.get('items') and isinstance(ocr_data.get('items'), list):
                items = ocr_data.get('items')
                if items:
                    ocr_message_parts.append("📋 %s:" % _("Items"))
                    
                    item_lines = []
                    
                    for item in items:
                        item_desc = item.get('description', '')
                        item_qty = item.get('quantity', '')
                        item_amount = item.get('amount', '')
                        
                        # Format each item line
                        item_parts = []
                        if item_qty:
                            item_parts.append(str(item_qty) + "×")
                        if item_desc:
                            item_parts.append(item_desc)
                        if item_amount:
                            item_parts.append("(" + str(item_amount) + ")")
                        
                        if item_parts:
                            item_lines.append("  • " + " ".join(item_parts))
                    
                    if item_lines:
                        ocr_message_parts.append("\n".join(item_lines))
            
            # Set the OCR message with all the details - use a larger field if available
            vals['ocr_status'] = 'processed'
            
            # Combine all parts into a single message
            full_message = "\n\n".join(ocr_message_parts)
            
            # Check if there's a larger field available for the full message
            if hasattr(self, 'ocr_details') and 'ocr_details' in self._fields:
                vals['ocr_details'] = full_message
                vals['ocr_message'] = _("✅ Receipt data successfully extracted. See details below.")[:2048]
            else:
                # If no larger field is available, truncate to fit in ocr_message
                vals['ocr_message'] = full_message[:2048]
                if len(full_message) > 2048:
                    _logger.info("OCR message truncated from %d to 2048 characters", len(full_message))
            
            self.write(vals)
            _logger.info("Updated expense %s with OCR data", self.id)
        else:
            self.write({
                'ocr_status': 'processed',
                'ocr_message': _("Receipt processed but no useful data was extracted.")[:2048]
            })
            _logger.warning("No useful data extracted from OCR for expense %s", self.id)
            
        return True
    
    def _find_product_by_normalized_code(self, products, normalized_code):
        """Manual search for a product by normalized default code."""
        for product in products:
            if product.default_code:
                normalized_product_code = product.default_code.strip().upper()
                if normalized_product_code == normalized_code:
                    return product
        return None
    
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
