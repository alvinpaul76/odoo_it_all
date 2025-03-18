-- SQL script to fix module uninstallation issues
-- Run this with: psql -U odoo -d odoo18_db -f fix_uninstall.sql

-- Drop the PostgreSQL function if it exists
DROP FUNCTION IF EXISTS process_receipt_scan(integer);

-- Get the module ID
\set ON_ERROR_STOP on
\set ECHO all

DO $$
DECLARE
    module_id INTEGER;
BEGIN
    -- Get the module ID
    SELECT id INTO module_id FROM ir_module_module WHERE name = 'hr_expense_claim_auto_scan';
    
    IF module_id IS NULL THEN
        RAISE NOTICE 'Module hr_expense_claim_auto_scan not found in the database';
        RETURN;
    END IF;
    
    RAISE NOTICE 'Module ID: %', module_id;
    
    -- Remove ir_model_data entries that reference ir.model.function
    DELETE FROM ir_model_data 
    WHERE model = 'ir.model.function' 
    AND module = 'hr_expense_claim_auto_scan';
    
    RAISE NOTICE 'Removed ir_model_data entries for ir.model.function';
    
    -- Set the module state to 'uninstalled'
    UPDATE ir_module_module 
    SET state = 'uninstalled' 
    WHERE id = module_id;
    
    RAISE NOTICE 'Set module state to uninstalled';
    
    -- Clean up any dependencies
    DELETE FROM ir_module_module_dependency
    WHERE module_id = module_id;
    
    RAISE NOTICE 'Cleaned up module dependencies';
    
    -- Commit the transaction
    RAISE NOTICE 'Database fix completed successfully';
END $$;

-- Final message
SELECT 'Module uninstallation fix completed. You can now reinstall or completely remove the module.' as result;
