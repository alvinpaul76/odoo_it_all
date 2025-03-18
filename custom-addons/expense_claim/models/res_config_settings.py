import logging
from odoo import models, fields

_logger = logging.getLogger(__name__)

class ResCompany(models.Model):
    _inherit = 'res.company'
    
    receipt_scanner_api_key = fields.Char(
        string="Receipt Scanner API Key",
        help="API key for the receipt scanning service"
    )
    receipt_scanner_api_url = fields.Char(
        string="Receipt Scanner API URL",
        help="URL endpoint for the receipt scanning service",
        default="https://api.receipt-scanner.com/v1/scan"
    )

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'
    
    receipt_scanner_api_key = fields.Char(
        related='company_id.receipt_scanner_api_key',
        string="Receipt Scanner API Key",
        help="API key for the receipt scanning service",
        readonly=False
    )
    receipt_scanner_api_url = fields.Char(
        related='company_id.receipt_scanner_api_url',
        string="Receipt Scanner API URL",
        help="URL endpoint for the receipt scanning service",
        readonly=False
    )
