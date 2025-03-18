# -*- coding: utf-8 -*-
import logging
from psycopg2 import Error as PostgresError

_logger = logging.getLogger(__name__)

def uninstall_hook(env):
    """
    Uninstall hook to clean up database objects created by this module.
    
    This function is called when the module is being uninstalled.
    It drops any PostgreSQL functions created by the module.
    
    Args:
        env: Odoo environment
    """
    _logger.info("Running uninstall hook for hr_expense_claim_auto_scan module")
    
    try:
        # Drop the PostgreSQL function if it exists
        env.cr.execute("DROP FUNCTION IF EXISTS process_receipt_scan(integer);")
        _logger.info("Successfully dropped PostgreSQL function 'process_receipt_scan'")
    except PostgresError as e:
        _logger.error("Error dropping PostgreSQL function: %s", str(e))
    
    # Clean up any ir.model.function records related to this module
    try:
        env.cr.execute("""
            DELETE FROM ir_model_data 
            WHERE model = 'ir.model.function' 
            AND module = 'hr_expense_claim_auto_scan'
        """)
        _logger.info("Successfully cleaned up ir.model.function records")
    except PostgresError as e:
        _logger.error("Error cleaning up ir.model.function records: %s", str(e))
