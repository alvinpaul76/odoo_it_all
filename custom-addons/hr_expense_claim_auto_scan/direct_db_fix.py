#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Direct database fix for Odoo module uninstallation.
This script directly modifies the Odoo database to fix the 'ir.model.function' error.

Usage:
    python3 direct_db_fix.py --db-name odoo --db-user odoo --db-password your_password
"""
import argparse
import logging
import psycopg2
from psycopg2 import Error as PostgresError

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
_logger = logging.getLogger(__name__)

def fix_database(db_name, db_user, db_password, db_host='localhost', db_port=5432):
    """
    Fix the database to allow module uninstallation.
    
    Args:
        db_name: Database name
        db_user: Database user
        db_password: Database password
        db_host: Database host (default: localhost)
        db_port: Database port (default: 5432)
    """
    module_name = 'hr_expense_claim_auto_scan'
    _logger.info("Starting database fix for %s module", module_name)
    
    try:
        # Connect to the database
        conn = psycopg2.connect(
            dbname=db_name,
            user=db_user,
            password=db_password,
            host=db_host,
            port=db_port
        )
        conn.autocommit = True
        cursor = conn.cursor()
        
        # 1. Drop the PostgreSQL function
        _logger.info("Dropping PostgreSQL function 'process_receipt_scan'")
        cursor.execute("DROP FUNCTION IF EXISTS process_receipt_scan(integer);")
        
        # 2. Get the module ID
        cursor.execute("SELECT id FROM ir_module_module WHERE name = %s", (module_name,))
        module_id = cursor.fetchone()
        if not module_id:
            _logger.error("Module %s not found in the database", module_name)
            return False
        module_id = module_id[0]
        _logger.info("Module ID: %s", module_id)
        
        # 3. Remove ir_model_data entries that reference ir.model.function
        _logger.info("Removing ir_model_data entries for ir.model.function")
        cursor.execute("""
            DELETE FROM ir_model_data 
            WHERE model = 'ir.model.function' 
            AND module = %s
        """, (module_name,))
        
        # 4. Set the module state to 'to remove' to allow uninstallation
        _logger.info("Setting module state to 'to remove'")
        cursor.execute("""
            UPDATE ir_module_module 
            SET state = 'to remove' 
            WHERE id = %s
        """, (module_id,))
        
        # 5. Clean up any dependencies
        _logger.info("Cleaning up module dependencies")
        cursor.execute("""
            DELETE FROM ir_module_module_dependency
            WHERE module_id = %s
        """, (module_id,))
        
        # Close the connection
        cursor.close()
        conn.close()
        
        _logger.info("Database fix completed successfully")
        return True
        
    except PostgresError as e:
        _logger.error("Database error: %s", str(e))
        return False
    except Exception as e:
        _logger.error("Error during fix: %s", str(e))
        return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Fix database for module uninstallation')
    parser.add_argument('--db-name', required=True, help='Database name')
    parser.add_argument('--db-user', required=True, help='Database user')
    parser.add_argument('--db-password', required=True, help='Database password')
    parser.add_argument('--db-host', default='localhost', help='Database host (default: localhost)')
    parser.add_argument('--db-port', type=int, default=5432, help='Database port (default: 5432)')
    
    args = parser.parse_args()
    
    success = fix_database(
        args.db_name, 
        args.db_user, 
        args.db_password, 
        args.db_host, 
        args.db_port
    )
    
    if success:
        print("\n===== DATABASE FIX COMPLETED =====")
        print("The module has been set to 'to remove' state in the database.")
        print("You should now be able to uninstall it through the Odoo interface.")
        print("If you still encounter issues, you can run this command to completely remove it:")
        print(f"DELETE FROM ir_module_module WHERE name = '{module_name}';")
    else:
        print("\n===== DATABASE FIX FAILED =====")
        print("Check the logs for details.")
