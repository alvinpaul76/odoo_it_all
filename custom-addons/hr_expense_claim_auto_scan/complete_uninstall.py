#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Complete uninstall script for hr_expense_claim_auto_scan module.
This script handles all the edge cases during module uninstallation.

Usage:
    cd /path/to/odoo
    python3 -m odoo shell -d database_name < complete_uninstall.py
"""
import logging
import sys
from psycopg2 import Error as PostgresError

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
_logger = logging.getLogger(__name__)

def complete_uninstall():
    """Complete uninstallation of the hr_expense_claim_auto_scan module."""
    module_name = 'hr_expense_claim_auto_scan'
    
    try:
        _logger.info("Starting complete uninstallation of %s module", module_name)
        
        # Find the module
        module = env['ir.module.module'].search([('name', '=', module_name)], limit=1)
        if not module:
            _logger.error("Module %s not found", module_name)
            return False
            
        _logger.info("Found module %s with ID %s and state %s", module_name, module.id, module.state)
        
        # 1. Drop PostgreSQL function
        _logger.info("Dropping PostgreSQL function")
        env.cr.execute("DROP FUNCTION IF EXISTS process_receipt_scan(integer);")
        
        # 2. Find all models created by this module
        _logger.info("Finding models created by this module")
        module_models = env['ir.model'].search([('modules', 'like', module_name)])
        model_ids = module_models.ids
        model_names = module_models.mapped('model')
        
        _logger.info("Found %s models: %s", len(model_ids), model_names)
        
        # 3. Clean up mail activities for these models
        if model_ids:
            _logger.info("Cleaning up mail activities")
            env.cr.execute("""
                DELETE FROM mail_activity 
                WHERE res_model_id IN (
                    SELECT id FROM ir_model 
                    WHERE modules LIKE %s
                )
            """, ['%' + module_name + '%'])
        
        # 4. Clean up ir.model.data records
        _logger.info("Cleaning up ir.model.data records")
        data_records = env['ir.model.data'].search([
            ('module', '=', module_name)
        ])
        if data_records:
            _logger.info("Found %s ir.model.data records to delete", len(data_records))
            # Use SQL to avoid ORM constraints
            env.cr.execute("""
                DELETE FROM ir_model_data
                WHERE module = %s
            """, [module_name])
        
        # 5. Clean up ir.model.fields
        _logger.info("Cleaning up ir.model.fields records")
        env.cr.execute("""
            DELETE FROM ir_model_fields
            WHERE modules LIKE %s
        """, ['%' + module_name + '%'])
        
        # 6. Set module state to 'uninstalled'
        _logger.info("Setting module state to 'uninstalled'")
        module.write({'state': 'uninstalled'})
        
        # 7. Commit changes
        env.cr.commit()
        _logger.info("Changes committed to database")
        
        return True
    except Exception as e:
        _logger.error("Error during module uninstallation: %s", e)
        return False

# Execute the uninstallation
result = complete_uninstall()

if result:
    print("\n===== MODULE UNINSTALLATION COMPLETED =====")
    print("The module has been successfully uninstalled from the database.")
else:
    print("\n===== MODULE UNINSTALLATION FAILED =====")
    print("Check the logs for details.")

# Exit the Odoo shell
sys.exit(0)
