#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Direct Odoo database fix script.
This script uses the Odoo API to properly uninstall a module.

Usage:
    cd /path/to/odoo
    python3 -m odoo shell -d database_name < uninstall_module.py
"""
import logging
import sys

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
_logger = logging.getLogger(__name__)

def uninstall_module():
    """Uninstall the hr_expense_claim_auto_scan module directly."""
    module_name = 'hr_expense_claim_auto_scan'
    
    try:
        # Drop PostgreSQL function first
        _logger.info("Dropping PostgreSQL function")
        env.cr.execute("DROP FUNCTION IF EXISTS process_receipt_scan(integer);")
        
        # Find the module
        module = env['ir.module.module'].search([('name', '=', module_name)], limit=1)
        if not module:
            _logger.error("Module %s not found", module_name)
            return False
            
        _logger.info("Found module %s with ID %s and state %s", module_name, module.id, module.state)
        
        # Remove ir.model.data records that reference ir.model.function
        _logger.info("Removing ir.model.data records for ir.model.function")
        data_records = env['ir.model.data'].search([
            ('model', '=', 'ir.model.function'),
            ('module', '=', module_name)
        ])
        if data_records:
            _logger.info("Found %s ir.model.data records to delete", len(data_records))
            data_records.unlink()
        
        # Force module state to 'uninstalled'
        _logger.info("Setting module state to 'uninstalled'")
        module.write({'state': 'uninstalled'})
        
        # Remove dependencies
        _logger.info("Removing module dependencies")
        env.cr.execute("""
            DELETE FROM ir_module_module_dependency
            WHERE module_id = %s
        """, (module.id,))
        
        # Commit changes
        env.cr.commit()
        _logger.info("Changes committed to database")
        
        return True
    except Exception as e:
        _logger.error("Error during module uninstallation: %s", e)
        return False

# Execute the uninstallation
result = uninstall_module()

if result:
    print("\n===== MODULE UNINSTALLATION COMPLETED =====")
    print("The module has been successfully uninstalled from the database.")
else:
    print("\n===== MODULE UNINSTALLATION FAILED =====")
    print("Check the logs for details.")

# Exit the Odoo shell
sys.exit(0)
