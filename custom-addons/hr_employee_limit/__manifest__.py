{
    'name': 'HR Employee Limit',
    'version': '1.0',
    'category': 'Human Resources',
    'summary': 'Limit the number of employees that can be created',
    'description': '''
This module adds a constraint to limit the number of employees that can be created in the system.
Once the limit is reached, no new employees can be created.
    ''',
    'author': 'Alvin Paul L. Azurin',
    'website': 'https://www.cre8or-lab.com',
    'depends': ['hr'],
    'data': [
        'security/ir.model.access.csv',
        'views/hr_employee_limit_views.xml',
        'data/hr_employee_limit_data.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}