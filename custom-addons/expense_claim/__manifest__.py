{
    'name': 'Expense Claim with Receipt Scanning',
    'version': '1.0',
    'category': 'Human Resources/Expenses',
    'summary': 'Scan receipts to automatically populate expense claims',
    'description': """
        This module extends the expense management functionality by adding
        receipt scanning capabilities. Upload a receipt image and the system
        will automatically extract relevant information to populate expense claim fields.
    """,
    'author': 'Odoo Developer',
    'website': '',
    'depends': ['hr_expense'],
    'data': [
        'security/ir.model.access.csv',
        'views/expense_claim_views.xml',
        'views/res_config_settings_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
