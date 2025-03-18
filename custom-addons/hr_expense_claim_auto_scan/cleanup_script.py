#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cleanup script for hr_expense_claim_auto_scan module.
This script directly cleans up database objects that might prevent module uninstallation.
"""
import argparse
import logging
import psycopg2
from psycopg2 import Error as PostgresError

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
_logger = logging.getLogger(__name__)

def cleanup_database(db_name, db_user, db_password, db_host='localhost', db_port=5432):
    """
    Clean up database objects related to hr_expense_claim_auto_scan module.
    
    Args:
        db_name: Database name
        db_user: Database user
        db_password: Database password
        db_host: Database host (default: localhost)
        db_port: Database port (default: 5432)
    """
    _logger.info("Starting database cleanup for hr_expense_claim_auto_scan module")
    
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
        
        # Drop PostgreSQL function if it exists
        _logger.info("Dropping PostgreSQL function 'process_receipt_scan'")
        cursor.execute("DROP FUNCTION IF EXISTS process_receipt_scan(integer);")
        
        # Clean up ir.model.function records
        _logger.info("Cleaning up ir.model.function records")
        cursor.execute("""
            DELETE FROM ir_model_data 
            WHERE model = 'ir.model.function' 
            AND module = 'hr_expense_claim_auto_scan';
        """)
        
        # Clean up ir_model_relation records
        _logger.info("Cleaning up ir_model_relation records")
        cursor.execute("""
            DELETE FROM ir_model_relation
            WHERE module = (
                SELECT id FROM ir_module_module 
                WHERE name = 'hr_expense_claim_auto_scan'
            );
        """)
        
        # Clean up ir_model_constraint records
        _logger.info("Cleaning up ir_model_constraint records")
        cursor.execute("""
            DELETE FROM ir_model_constraint
            WHERE module = (
                SELECT id FROM ir_module_module 
                WHERE name = 'hr_expense_claim_auto_scan'
            );
        """)
        
        # Clean up ir_model_data records
        _logger.info("Cleaning up ir_model_data records for ir.model.function")
        cursor.execute("""
            DELETE FROM ir_model_data
            WHERE model = 'ir.model.function'
            AND module = 'hr_expense_claim_auto_scan';
        """)
        
        # Close the connection
        cursor.close()
        conn.close()
        
        _logger.info("Database cleanup completed successfully")
        return True
        
    except PostgresError as e:
        _logger.error("Database error: %s", str(e))
        return False
    except Exception as e:
        _logger.error("Error during cleanup: %s", str(e))
        return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Clean up database objects for hr_expense_claim_auto_scan module')
    parser.add_argument('--db-name', required=True, help='Database name')
    parser.add_argument('--db-user', required=True, help='Database user')
    parser.add_argument('--db-password', required=True, help='Database password')
    parser.add_argument('--db-host', default='localhost', help='Database host (default: localhost)')
    parser.add_argument('--db-port', type=int, default=5432, help='Database port (default: 5432)')
    
    args = parser.parse_args()
    
    success = cleanup_database(
        args.db_name, 
        args.db_user, 
        args.db_password, 
        args.db_host, 
        args.db_port
    )
    
    if success:
        print("Cleanup completed successfully. You can now try to uninstall the module.")
    else:
        print("Cleanup failed. Check the logs for details.")
