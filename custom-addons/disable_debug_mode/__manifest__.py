{
    'name': 'Disable Debug Mode for Non-Admin Users',
    'version': '1.0',
    'category': 'Technical',
    'summary': 'Restricts debug mode access to admin users only',
    'description': '''
This module prevents non-admin users from accessing debug mode in Odoo.
It intercepts debug mode requests (?debug=1) in the URL and redirects 
non-admin users to the same page without debug mode enabled.

Key features:
- Restricts debug mode to admin users only
- Prevents URL manipulation to access debug mode
- Maintains normal functionality for admin users
- No configuration needed - works automatically after installation
    ''',
    'author': 'Alvin Paul L. Azurin',
    'website': 'https://www.cre8or-lab.com',
    'depends': ['web', 'base'],
    'data': [
        'security/ir.model.access.csv',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
