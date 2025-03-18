import base64
import logging
import requests
import json
from datetime import datetime
from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

class HrExpense(models.Model):
    _inherit = 'hr.expense'
    
    # Fields defined in this model
    scanned_receipt = fields.Boolean(string="Receipt Scanned", default=False, 
                                     help="Indicates if the receipt has been scanned and data extracted")
    confidence_score = fields.Float(string="Scan Confidence", default=0.0, 
                                   help="Confidence score of the receipt scanning")
    scan_date = fields.Datetime(string="Scan Date", 
                               help="Date and time when the receipt was scanned")
    scan_message = fields.Text(string="Scan Message", 
                              help="Message returned by the scanning service")
    
    def action_scan_receipt(self):
        """Scan the attached receipt and extract information"""
        self.ensure_one()
        
        # Get the main attachment from mail.thread functionality
        attachment = self.sudo().message_main_attachment_id
        if not attachment:
            raise UserError(_("Please attach a receipt before scanning."))
            
        # Check if API key is configured in company settings
        company = self.env.company
        if not company.receipt_scanner_api_key:
            raise UserError(_("Receipt scanner API key is not configured. Please configure it in Settings."))
            
        # Check if the attachment is an image or PDF
        mimetype = attachment.mimetype
        if not (mimetype and (mimetype.startswith('image/') or mimetype == 'application/pdf')):
            raise UserError(_("The attached file must be an image or PDF."))
            
        try:
            # Log the start of scanning process
            _logger.info(
                "Starting receipt scanning for expense id: %s, attachment id: %s, user: %s", 
                self.id, attachment.id, self.env.user.name
            )
            
            # Get file content
            file_content = base64.b64decode(attachment.datas)
            
            # Call receipt scanning API
            api_url = company.receipt_scanner_api_url or "https://api.receipt-scanner.com/v1/scan"
            api_key = company.receipt_scanner_api_key
            
            # Prepare the request data
            # Create a multipart form data request with both the receipt file and additional data
            files = {
                'receipt': (attachment.name, file_content, mimetype)
            }
            
            # Add additional data as needed by the API
            data = {
                'expense_id': str(self.id),
                'employee': self.employee_id.name if self.employee_id else '',
                'description': self.name or '',
                'company': company.name,
                'request_timestamp': datetime.now().isoformat()
            }
            
            headers = {
                'Authorization': f'Bearer {api_key}'
                # Content-Type will be set automatically by requests for multipart/form-data
            }
            
            # Log API request (without sensitive data)
            _logger.info(
                "Sending request to receipt scanner API: %s for expense id: %s with data: %s", 
                api_url, self.id, json.dumps({k: v for k, v in data.items() if k != 'api_key'})
            )
            
            response = requests.post(
                api_url,
                headers=headers,
                data=data,
                files=files,
                timeout=30
            )
            
            # Log API response status
            _logger.info(
                "Receipt scanner API response status: %s for expense id: %s", 
                response.status_code, self.id
            )
            
            if response.status_code != 200:
                error_message = f"Receipt scanning failed with status code: {response.status_code}"
                _logger.error(
                    "%s for expense id: %s, response: %s", 
                    error_message, self.id, response.text
                )
                raise UserError(_(error_message))
                
            # Parse response
            result = response.json()
            
            # Log the response structure for debugging
            _logger.debug("API response structure: %s, content: %s", type(result), json.dumps(result)[:500])
            
            # Handle different response formats (list or dict)
            if isinstance(result, list):
                if result:
                    # Take the first item if it's a list
                    _logger.info("API returned a list of results, using the first item")
                    result = result[0] if isinstance(result[0], dict) else {"output": {}}
                else:
                    # Empty list
                    _logger.warning("API returned an empty list for expense id: %s", self.id)
                    result = {"output": {}}
            
            # Update expense with extracted data
            self._update_from_scan_result(result)
            
            # Log successful scan
            _logger.info(
                "Receipt successfully scanned for expense id: %s with confidence: %s", 
                self.id, self.confidence_score
            )
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Receipt Scanned'),
                    'message': _('Receipt has been successfully scanned and expense details updated.'),
                    'sticky': False,
                    'type': 'success',
                }
            }
            
        except requests.exceptions.RequestException as e:
            error_message = f"Error connecting to receipt scanner API: {str(e)}"
            _logger.error(
                "%s for expense id: %s", 
                error_message, self.id
            )
            raise UserError(_(error_message)) from e
            
        except Exception as e:
            error_message = f"Error scanning receipt: {str(e)}"
            _logger.error(
                "%s for expense id: %s", 
                error_message, self.id, 
                exc_info=True
            )
            raise UserError(_(error_message)) from e
    
    def _update_from_scan_result(self, result):
        """Update expense fields from scan result"""
        # Ensure result is a dictionary
        if not isinstance(result, dict):
            _logger.error(
                "Invalid result format for expense id: %s, expected dict but got %s", 
                self.id, type(result)
            )
            result = {"output": {}}
            
        # Initialize values dictionary for updating the expense
        vals = {
            'scanned_receipt': True,
            'scan_date': fields.Datetime.now(),
            'confidence_score': 1.0,  # Default confidence score
            'scan_message': json.dumps(result, indent=2)
        }
        
        # Extract data from scan result - handle the specific API response format
        # The API returns data in the 'output' field
        output = result.get('output', {})
        if not output:
            _logger.warning("No 'output' field found in API response for expense id: %s", self.id)
            output = {}
            
        _logger.info("Processing output data: %s for expense id: %s", json.dumps(output), self.id)
        
        # Update expense fields based on scan results
        # Business name as merchant
        if 'business_name' in output:
            vals['name'] = output.get('business_name', '')
            _logger.info("Set merchant name to: %s for expense id: %s", vals['name'], self.id)
            
        # Handle date field
        if 'date' in output:
            try:
                date_str = output.get('date', '')
                _logger.info("Attempting to parse date: %s for expense id: %s", date_str, self.id)
                
                # Try to parse the specific date format from the example: "Jun 28, 15 01:35 PM"
                try:
                    date_obj = datetime.strptime(date_str, "%b %d, %y %I:%M %p")
                    vals['date'] = date_obj.strftime('%Y-%m-%d')
                    _logger.info("Successfully parsed date to: %s for expense id: %s", vals['date'], self.id)
                except ValueError as e:
                    _logger.warning(
                        "Failed to parse date with specific format for expense id: %s, date value: %s, error: %s", 
                        self.id, date_str, str(e)
                    )
                    # Try other common formats
                    for fmt in ['%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y', '%b %d, %Y', '%B %d, %Y']:
                        try:
                            date_obj = datetime.strptime(date_str, fmt)
                            vals['date'] = date_obj.strftime('%Y-%m-%d')
                            _logger.info("Successfully parsed date with format %s to: %s for expense id: %s", 
                                        fmt, vals['date'], self.id)
                            break
                        except ValueError:
                            continue
            except Exception as e:
                _logger.warning(
                    "Failed to parse date from receipt scan for expense id: %s, date value: %s, error: %s", 
                    self.id, output.get('date', ''), str(e)
                )
        
        # Handle financial information
        subtotal = 0.0
        tax = 0.0
        total = 0.0
        
        # Get subtotal (amount before tax)
        if 'subtotal' in output:
            try:
                subtotal = float(output.get('subtotal', 0.0))
                _logger.info("Extracted subtotal: %s for expense id: %s", subtotal, self.id)
            except (ValueError, TypeError) as e:
                _logger.warning(
                    "Failed to parse subtotal from receipt scan for expense id: %s, value: %s, error: %s", 
                    self.id, output.get('subtotal'), str(e)
                )
        
        # Get tax amount - try multiple possible field names
        tax_field_names = ['tax', 'taxes', 'tax_amount', 'vat', 'gst', 'hst']
        for tax_field in tax_field_names:
            if tax_field in output:
                try:
                    tax_value = output.get(tax_field, 0.0)
                    # Handle case where tax might be a list of tax items
                    if isinstance(tax_value, list):
                        tax = sum(float(item.get('amount', 0.0)) for item in tax_value if isinstance(item, dict))
                    else:
                        tax = float(tax_value)
                    _logger.info("Extracted tax amount from field '%s': %s for expense id: %s", 
                                tax_field, tax, self.id)
                    break
                except (ValueError, TypeError) as e:
                    _logger.warning(
                        "Failed to parse tax amount from field '%s' for expense id: %s, value: %s, error: %s", 
                        tax_field, self.id, output.get(tax_field), str(e)
                    )
        
        # Get total amount - try multiple possible field names
        total_field_names = ['total_amount', 'total', 'amount', 'grand_total']
        for total_field in total_field_names:
            if total_field in output:
                try:
                    total = float(output.get(total_field, 0.0))
                    _logger.info("Extracted total amount from field '%s': %s for expense id: %s", 
                                total_field, total, self.id)
                    break
                except (ValueError, TypeError) as e:
                    _logger.warning(
                        "Failed to parse total amount from field '%s' for expense id: %s, value: %s, error: %s", 
                        total_field, self.id, output.get(total_field), str(e)
                    )
        
        # If we have total but no tax, try to calculate tax from subtotal and total
        if total > 0 and subtotal > 0 and tax == 0:
            calculated_tax = total - subtotal
            if calculated_tax > 0:
                tax = calculated_tax
                _logger.info(
                    "Calculated tax as total(%s) - subtotal(%s) = %s for expense id: %s", 
                    total, subtotal, tax, self.id
                )
        
        # Validate financial data consistency
        if total > 0 and subtotal > 0 and tax > 0:
            # Check if the total equals subtotal + tax (within a small margin for rounding errors)
            calculated_total = subtotal + tax
            if abs(calculated_total - total) < 0.01:
                _logger.info(
                    "Financial data is consistent: subtotal(%s) + tax(%s) = total(%s) for expense id: %s", 
                    subtotal, tax, total, self.id
                )
            else:
                _logger.warning(
                    "Financial data inconsistency: subtotal(%s) + tax(%s) = %s, but total = %s for expense id: %s", 
                    subtotal, tax, calculated_total, total, self.id
                )
        
        # Update financial fields - directly set the fields that are not computed
        if subtotal > 0:
            # For Odoo, we need to set both total_amount and total_amount_currency
            vals['total_amount'] = subtotal
            vals['total_amount_currency'] = subtotal
            _logger.info("Set total_amount and total_amount_currency to subtotal: %s for expense id: %s", subtotal, self.id)
        elif total > 0 and tax > 0:
            # If we have total and tax but no subtotal, calculate it
            calculated_subtotal = total - tax
            vals['total_amount'] = calculated_subtotal
            vals['total_amount_currency'] = calculated_subtotal
            _logger.info(
                "Calculated and set total_amount and total_amount_currency as total(%s) - tax(%s) = %s for expense id: %s", 
                total, tax, calculated_subtotal, self.id
            )
        elif total > 0:
            # If we only have total, use it as is
            vals['total_amount'] = total
            vals['total_amount_currency'] = total
            _logger.info("Set total_amount and total_amount_currency to total: %s for expense id: %s", total, self.id)
            
        # Set tax amount if available - directly set both tax fields
        if tax > 0:
            vals['tax_amount'] = tax
            vals['tax_amount_currency'] = tax
            _logger.info("Set tax_amount and tax_amount_currency to: %s for expense id: %s", tax, self.id)
            
        # Process receipt items if available
        if 'items' in output and isinstance(output['items'], list) and output['items']:
            items_description = []
            total_tax = 0.0
            
            for item in output['items']:
                if isinstance(item, dict):
                    qty = item.get('quantity', '')
                    desc = item.get('description', '')
                    amount = item.get('amount', '')
                    item_tax = 0.0
                    
                    # Try to extract tax from item
                    try:
                        if 'tax' in item:
                            item_tax = float(item.get('tax', 0.0))
                            total_tax += item_tax
                    except (ValueError, TypeError):
                        pass
                    
                    if desc:
                        item_text = f"{qty} x {desc}" if qty else desc
                        item_text += f": {amount}" if amount else ""
                        if item_tax > 0:
                            item_text += f" (Tax: {item_tax})"
                        items_description.append(item_text)
            
            # If we calculated a total tax from items and it's different from the overall tax
            if total_tax > 0 and (tax == 0 or abs(total_tax - tax) > 0.01):
                _logger.info(
                    "Updating tax amount from sum of item taxes: %s for expense id: %s (previous value: %s)", 
                    total_tax, self.id, tax
                )
                vals['tax_amount'] = total_tax
                vals['tax_amount_currency'] = total_tax
            
            if items_description:
                # If we have items, add them to the description
                current_description = self.description or ""
                items_summary = "\n".join(items_description)
                new_description = f"{current_description}\n\nReceipt Items:\n{items_summary}" if current_description else f"Receipt Items:\n{items_summary}"
                vals['description'] = new_description
                _logger.info("Added receipt items to description for expense id: %s", self.id)
        
        # Update the expense with all values at once
        _logger.info(
            "Updating expense id: %s with values: %s", 
            self.id, json.dumps({k: str(v) for k, v in vals.items() if k != 'scan_message'})
        )
        
        # Force update the fields directly to bypass computed fields
        self.sudo().write(vals)
        
        # Log the updated values
        _logger.info(
            "Updated expense id: %s with values: %s", 
            self.id, json.dumps({k: str(v) for k, v in vals.items() if k != 'scan_message'})
        )
