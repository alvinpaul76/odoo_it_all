import logging
import json
from odoo import http, _
from odoo.http import request
from odoo.exceptions import AccessError, UserError

_logger = logging.getLogger(__name__)

class ExpenseClaimController(http.Controller):
    """Controller for expense claim receipt scanning webhook callbacks"""
    
    @http.route('/expense_claim/webhook', type='json', auth='public', csrf=False)
    def receipt_scan_webhook(self, **post):
        """Handle webhook callbacks from the receipt scanning service"""
        # Log the webhook call
        _logger.info(
            "Received receipt scan webhook callback from %s", 
            request.httprequest.remote_addr
        )
        
        try:
            # Extract data from the request
            data = json.loads(request.httprequest.data.decode('utf-8'))
            
            # Validate the webhook token if configured
            company = request.env['res.company'].sudo().search([], limit=1)
            webhook_token = company.receipt_scanner_api_key
            
            if not webhook_token:
                _logger.error("Receipt scanner webhook token not configured")
                return {'status': 'error', 'message': 'Webhook token not configured'}
            
            # Verify the token from the request header
            auth_header = request.httprequest.headers.get('Authorization', '')
            if not auth_header.startswith('Bearer ') or auth_header[7:] != webhook_token:
                _logger.error(
                    "Invalid webhook token received from %s", 
                    request.httprequest.remote_addr
                )
                return {'status': 'error', 'message': 'Invalid webhook token'}
            
            # Process the webhook data
            expense_id = data.get('expense_id')
            scan_result = data.get('scan_result')
            
            if not expense_id or not scan_result:
                _logger.error(
                    "Invalid webhook data: missing expense_id or scan_result from %s", 
                    request.httprequest.remote_addr
                )
                return {'status': 'error', 'message': 'Invalid webhook data'}
            
            # Find the expense record
            expense = request.env['hr.expense'].sudo().browse(int(expense_id))
            if not expense.exists():
                _logger.error(
                    "Expense record not found for ID: %s from webhook call from %s", 
                    expense_id, request.httprequest.remote_addr
                )
                return {'status': 'error', 'message': 'Expense record not found'}
            
            # Update the expense with the scan result
            try:
                expense._update_from_scan_result(scan_result)
                _logger.info(
                    "Successfully updated expense ID: %s from webhook callback", 
                    expense_id
                )
                return {'status': 'success', 'message': 'Expense updated successfully'}
            except Exception as e:
                _logger.error(
                    "Error updating expense from webhook: %s for expense ID: %s", 
                    str(e), expense_id, 
                    exc_info=True
                )
                return {'status': 'error', 'message': f'Error updating expense: {str(e)}'}
                
        except json.JSONDecodeError as e:
            _logger.error(
                "Invalid JSON in webhook request: %s from %s", 
                str(e), request.httprequest.remote_addr
            )
            return {'status': 'error', 'message': 'Invalid JSON in request'}
            
        except Exception as e:
            _logger.error(
                "Unexpected error in webhook processing: %s from %s", 
                str(e), request.httprequest.remote_addr, 
                exc_info=True
            )
            return {'status': 'error', 'message': f'Unexpected error: {str(e)}'}
