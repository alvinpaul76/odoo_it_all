# HR Expense Claim Auto Scan

## Overview
This module extends the HR Expense functionality in Odoo 18 to allow automatic scanning and extraction of data from expense receipts using OCR API technology. It enables users to upload receipt images (JPG, PNG, PDF) and automatically extracts key information to populate expense claims without requiring manual intervention.

## Features
- **Automatic Receipt Scanning**: Receipts are automatically scanned as soon as they are attached to an expense
- **Real-time Status Updates**: Visual indicators show the current status of receipt scanning (pending, processed, failed)
- **Data Extraction**: Extract key information such as vendor name, date, amount, receipt number, and tax information
- **Auto-Fill Expense Form**: Automatically populate expense claim fields with extracted data
- **User Review & Editing**: Preview extracted details for user verification and modification
- **Comprehensive Logging**: Detailed server-side logs for debugging and audit purposes
- **Line Item Support**: Extracts individual line items from receipts with descriptions and amounts

## Technical Information

### Dependencies
- Odoo 18 HR Expense module (`hr_expense`)
- External OCR API service (configurable)

### Configuration
1. **API Credentials**: Set up the OCR API credentials in Odoo system parameters:
   - `ocr_api_key`: Your OCR service API key
   - `ocr_api_url`: The OCR service endpoint URL
   - `ocr_test_mode`: Set to 'True' to enable test mode (returns mock data without calling the API)

2. **Security**: The module uses Odoo's standard security groups:
   - Users must have `hr_expense.group_hr_expense_user` access rights to scan receipts

### OCR Response Format
The module supports two OCR response formats:

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

The module automatically detects the format and processes it accordingly.

### Usage
1. Create a new expense
2. Attach a receipt image (JPG, PNG) or PDF document
3. The system will automatically process the receipt and extract data
4. A status indicator will show the progress (pending, processed, failed)
5. Review the extracted information and make any necessary adjustments
6. Submit the expense claim as usual

### Manual Scanning
If needed, you can also manually trigger scanning:
1. Attach a receipt to an expense that hasn't been scanned yet
2. Open the attachment view
3. The system will process the receipt and show a notification with the result

### Technical Implementation
- **Models**: Extends `hr.expense` model with OCR-related fields and methods
- **Services**: Contains OCR processing logic and API integration
- **Views**: Enhances expense form, list, and kanban views with OCR status indicators
- **Asynchronous Processing**: Immediate processing of receipts when attachments are added

## Logging
The module implements comprehensive logging for debugging purposes:
- All OCR requests and responses are logged with timestamps
- Processing errors are captured with detailed context
- Field mapping and data extraction steps are logged
- Line item processing is logged with item counts and details

## Error Handling
- User-friendly error messages are displayed for failed operations
- Detailed error information is logged server-side
- Graceful exception handling prevents system crashes
- Scan messages provide specific information about failures
- Special handling for webhook errors with mock data fallback

## Testing
The module includes test utilities to verify OCR functionality:
- Test scripts for both new and legacy response formats
- Mock data generation for testing without API access
- Test mode parameter to bypass actual API calls

## Security Considerations
- API keys are stored securely in Odoo system parameters
- Access controls restrict who can scan receipts
- No sensitive information is exposed in client-side code
- Proper error handling prevents exposure of system details

## Support and Maintenance
For questions, issues, or feature requests, please contact the module maintainer or submit an issue through the standard Odoo issue tracking system.

## License
This module is licensed under LGPL-3.
