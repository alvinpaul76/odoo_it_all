import logging
import psycopg2
from odoo import api, models

_logger = logging.getLogger(__name__)

class InitFunctions(models.AbstractModel):
    _name = 'hr_expense_claim_auto_scan.init_functions'
    _description = 'Initialize PostgreSQL Functions for OCR'

    @api.model
    def init(self):
        """Initialize PostgreSQL functions when the module is installed or updated."""
        _logger.info("Initializing PostgreSQL functions for OCR scanning")
        
        # Check if the function already exists
        try:
            self.env.cr.execute("""
                SELECT proname FROM pg_proc 
                WHERE proname = 'process_receipt_scan'
            """)
            function_exists = self.env.cr.fetchone()
            
            if function_exists:
                _logger.info("Function 'process_receipt_scan' already exists, updating it")
            else:
                _logger.info("Function 'process_receipt_scan' doesn't exist, creating it")
            
            # Create or replace the process_receipt_scan function
            self.env.cr.execute("""
                CREATE OR REPLACE FUNCTION process_receipt_scan(expense_id integer) RETURNS void AS $$
                BEGIN
                    -- Call the expense model's process_receipt_scan method
                    PERFORM dblink_exec('dbname=' || current_database(),
                        'UPDATE hr_expense SET ocr_status = ''processing'' WHERE id = ' || expense_id);
                    
                    -- Execute the Python method to process the receipt
                    PERFORM dblink_exec('dbname=' || current_database(),
                        'SELECT auto_scan_attachment(message_main_attachment_id) FROM hr_expense WHERE id = ' || expense_id);
                    
                    -- Log the execution for debugging purposes
                    RAISE NOTICE 'Process receipt scan executed for expense_id: %', expense_id;
                END;
                $$ LANGUAGE plpgsql;
            """)
            
            # Verify the function was created successfully
            self.env.cr.execute("""
                SELECT proname FROM pg_proc 
                WHERE proname = 'process_receipt_scan'
            """)
            if self.env.cr.fetchone():
                _logger.info("PostgreSQL function 'process_receipt_scan' created/updated successfully")
            else:
                _logger.error("Failed to create PostgreSQL function 'process_receipt_scan'")
                
        except psycopg2.Error as e:
            _logger.error("Error creating PostgreSQL function: %s", str(e))
            # Don't raise the exception to prevent installation failure
            # Just log the error for debugging
