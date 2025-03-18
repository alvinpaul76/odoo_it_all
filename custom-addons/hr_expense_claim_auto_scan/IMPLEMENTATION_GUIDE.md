# HR Expense OCR Implementation Guide

## Overview

This guide documents the implementation of OCR response format handling in the HR Expense Claim Auto Scan module. The module now supports both the new structured format (with nested `output` field) and the legacy flat format.

## Changes Implemented

### 1. OCR Response Format Handling

The module has been enhanced to handle two OCR response formats:

#### New Format (Nested Structure)
```json
{
  "output": {
    "business_name": "Vibasel Outlets",
    "receipt_number": "8901",
    "date": "10/25/2017 10:36 PM",
    "items": [
      {
        "quantity": 1,
        "description": "HNRY BPCK PBB LEATHE;OXB",
        "amount": 261.75
      },
      {
        "quantity": 1,
        "description": "WHRN CTSR PEB BELT;BLK/D",
        "amount": 51.75
      }
    ],
    "subtotal": 375.5,
    "tax": 25.08,
    "total_amount": 400.58
  }
}
```

#### Legacy Format (Flat Structure)
```json
{
  "vendor": "Legacy Vendor Inc.",
  "receipt_number": "LR-12345",
  "date": "2023-01-15",
  "total": "299.99",
  "description": "Office supplies"
}
```

### 2. Key Implementation Details

1. **Format Detection**: The `update_from_ocr_result` method now automatically detects the format by checking for the presence of an `output` field.

2. **Field Mapping**: 
   - Business name is extracted from either `business_name` (new format) or `vendor` (legacy format)
   - Receipt number is extracted from `receipt_number` in both formats
   - Total amount is extracted from either `total_amount` (new format) or `total` (legacy format)
   - Date is extracted with support for multiple date formats

3. **Line Item Support**: The new format supports line items with quantity, description, and amount.

4. **Error Handling**: Comprehensive error handling with detailed logging has been implemented.

5. **Status Tracking**: OCR processing status is tracked with states: 'pending', 'processed', 'failed'.

### 3. Code Structure Changes

1. **HR Expense Model**:
   - Added fields for OCR status, message, business name, and receipt number
   - Enhanced `auto_scan_attachment` method with better error handling
   - Improved `update_from_ocr_result` method to handle both formats
   - Added `action_scan_receipt` for manual scanning

2. **OCR Service**:
   - Added test mode support
   - Enhanced error handling for API calls
   - Improved logging for debugging

3. **Testing**:
   - Added manual test script for OCR processing
   - Added automated tests for format handling

## Testing Instructions

### Manual Testing

1. **Using the Shell Script**:
   ```bash
   cd /path/to/odoo
   ./custom-addons/hr_expense_claim_auto_scan/tests/run_manual_test.sh
   ```

2. **Using the Odoo Shell**:
   ```python
   # In Odoo shell
   from hr_expense_claim_auto_scan.tests.manual_test import test_ocr_new_format, test_ocr_legacy_format, test_ocr_service
   
   env = self.env  # Get the environment
   
   # Test with new format
   test_ocr_new_format(env)
   
   # Test with legacy format
   test_ocr_legacy_format(env)
   
   # Test OCR service
   test_ocr_service(env)
   ```

### Automated Testing

Run the automated tests with:
```bash
python odoo-bin -d <database> --test-enable --test-tags=hr_expense_claim_auto_scan
```

## Configuration

1. **API Credentials**:
   - Set `ocr_api_key` system parameter with your OCR service API key
   - Set `ocr_api_url` system parameter with the OCR service endpoint URL

2. **Test Mode**:
   - Set `ocr_test_mode` system parameter to 'True' to enable test mode (returns mock data)

## Logging

The module implements comprehensive logging:
- All OCR requests and responses are logged with timestamps
- Processing errors are captured with detailed context
- Field mapping and data extraction steps are logged

## Error Handling

- User-friendly error messages are displayed for failed operations
- Detailed error information is logged server-side
- Graceful exception handling prevents system crashes

## Best Practices

1. **Security**:
   - API keys are stored securely in Odoo system parameters
   - Access controls restrict who can scan receipts

2. **Performance**:
   - OCR processing is triggered only when necessary
   - Test mode is available for development without API calls

3. **User Experience**:
   - Clear status indicators show processing state
   - Informative messages explain any failures

## Troubleshooting

1. **OCR Processing Fails**:
   - Check the server logs for detailed error information
   - Verify API credentials are correctly set
   - Ensure the receipt file format is supported

2. **Incorrect Data Extraction**:
   - Check the OCR response format in the logs
   - Verify the receipt image quality
   - Consider manual data entry for poor quality receipts

3. **Database Connection Issues**:
   - Ensure PostgreSQL is running
   - Check database connection parameters
   - Verify Odoo has proper permissions to access the database

## Future Enhancements

1. **Additional Format Support**: Add support for more OCR service providers
2. **Enhanced Line Item Processing**: Improve mapping of line items to expense products
3. **Receipt Quality Check**: Add pre-processing to check receipt image quality
4. **Batch Processing**: Support for scanning multiple receipts in batch mode
