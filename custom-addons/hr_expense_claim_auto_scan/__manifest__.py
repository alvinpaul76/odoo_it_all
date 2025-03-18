# -*- coding: utf-8 -*-

{
    'name': 'HR Expense Claim Auto Scan',
    'version': '18.0.1.0.0',
    'summary': 'Automatically scan and extract data from expense receipts',
    'description': """
        This module extends the HR Expense functionality to allow automatic scanning
        and extraction of data from expense receipts using OCR API.
        
        Features:
        - Upload receipt images (jpg, png, pdf)
        - Automatically extract data using OCR API
        - Auto-fill expense claim form with extracted data
        - Allow users to review and edit extracted data
    """,
    'category': 'Human Resources/Expenses',
    'author': 'Odoo SA',
    'website': 'https://www.odoo.com',
    'depends': ['hr_expense'],
    'data': [
        'security/ir.model.access.csv',
        'views/hr_expense_views.xml',
        'data/system_parameters.xml',
    ],
    'uninstall_hook': 'uninstall_hook',
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
