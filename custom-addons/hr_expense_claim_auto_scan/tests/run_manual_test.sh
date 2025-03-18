#!/bin/bash
# Script to run manual OCR tests in Odoo shell

# Change to the Odoo directory
cd /Volumes/T7/Workspace/dev_apps/odoo/odoo

# Run the Odoo shell with the following script
# This will execute our manual tests and show the results
python odoo-bin shell -d odoo --no-http << EOF
import sys
sys.path.append('/Volumes/T7/Workspace/dev_apps/odoo/odoo/custom-addons')
from hr_expense_claim_auto_scan.tests.manual_test import test_ocr_new_format, test_ocr_legacy_format, test_ocr_service

print("\n===== Testing OCR with new format =====")
test_ocr_new_format(env)

print("\n===== Testing OCR with legacy format =====")
test_ocr_legacy_format(env)

print("\n===== Testing OCR service with mock data =====")
test_ocr_service(env)

print("\n===== All tests completed =====")
EOF
