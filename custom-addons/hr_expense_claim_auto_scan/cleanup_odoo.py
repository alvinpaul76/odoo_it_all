# -*- coding: utf-8 -*-
"""
Odoo shell script to clean up ir.model.function records.
Run this script using the Odoo shell:
    python3 odoo-bin shell -d your_database -c your_config_file --no-http < cleanup_odoo.py
"""
import logging
import sys

_logger = logging.getLogger(__name__)
_logger.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
_logger.addHandler(handler)

def cleanup_module_data():
    """Clean up database records that prevent module uninstallation."""
    module_name = 'hr_expense_claim_auto_scan'
    
    _logger.info("Starting cleanup for module: %s", module_name)
    
    # Get the module record
    module = env['ir.module.module'].search([('name', '=', module_name)], limit=1)
    if not module:
        _logger.error("Module %s not found in the database", module_name)
        return False
    
    _logger.info("Found module with ID: %s", module.id)
    
    # Clean up ir.model.function records
    _logger.info("Cleaning up ir.model.function records")
    model_function_data = env['ir.model.data'].search([
        ('model', '=', 'ir.model.function'),
        ('module', '=', module_name)
    ])
    
    if model_function_data:
        _logger.info("Found %s ir.model.function data records", len(model_function_data))
        model_function_data.unlink()
        _logger.info("Deleted ir.model.function data records")
    else:
        _logger.info("No ir.model.function data records found")
    
    # Try to find and delete the actual ir.model.function records
    # This is a bit tricky as ir.model.function might not be accessible directly
    try:
        # Try to access the model directly
        if 'ir.model.function' in env:
            model_functions = env['ir.model.function'].search([])
            if model_functions:
                _logger.info("Found %s ir.model.function records", len(model_functions))
                model_functions.unlink()
                _logger.info("Deleted ir.model.function records")
            else:
                _logger.info("No ir.model.function records found")
    except Exception as e:
        _logger.warning("Could not access ir.model.function directly: %s", str(e))
        # Try with direct SQL as a fallback
        try:
            _logger.info("Trying direct SQL approach")
            env.cr.execute("DELETE FROM ir_model_function WHERE module_id = %s", (module.id,))
            _logger.info("Executed SQL cleanup")
        except Exception as e:
            _logger.error("SQL cleanup failed: %s", str(e))
    
    # Clean up ir_model_constraint records
    _logger.info("Cleaning up ir_model_constraint records")
    env.cr.execute("""
        DELETE FROM ir_model_constraint
        WHERE module = %s
    """, (module.id,))
    
    # Clean up ir_model_relation records
    _logger.info("Cleaning up ir_model_relation records")
    env.cr.execute("""
        DELETE FROM ir_model_relation
        WHERE module = %s
    """, (module.id,))
    
    # Execute direct SQL to drop the function if it exists
    _logger.info("Dropping PostgreSQL function")
    try:
        env.cr.execute("DROP FUNCTION IF EXISTS process_receipt_scan(integer)")
        _logger.info("PostgreSQL function dropped successfully")
    except Exception as e:
        _logger.error("Error dropping PostgreSQL function: %s", str(e))
    
    # Commit the changes
    env.cr.commit()
    _logger.info("Changes committed to database")
    
    return True

# Execute the cleanup
try:
    result = cleanup_module_data()
    if result:
        print("\n===== CLEANUP SUCCESSFUL =====")
        print("You can now try to uninstall the module")
    else:
        print("\n===== CLEANUP FAILED =====")
        print("Check the logs for details")
except Exception as e:
    _logger.error("Cleanup failed with error: %s", str(e))
    print("\n===== CLEANUP FAILED =====")
    print(f"Error: {str(e)}")
