# -*- coding: utf-8 -*-
{
    'name': 'User Limit',
    'version': '1.0',
    'summary': 'Limit the number of users that can be created',
    'description': """
        This module allows administrators to set a maximum limit on the number of users
        that can be created in the system.
    """,
    'category': 'Administration',
    'author': 'Alvin Paul L. Azurin',
    'website': 'https://www.cre8or-lab.com',
    'license': 'LGPL-3',
    'depends': ['base'],
    'data': [
        'security/ir.model.access.csv',
        'views/res_user_limit_views.xml',
        'data/res_user_limit_data.xml',
    ],
    'installable': True,
    'auto_install': False,
}
