# -*- coding: utf-8 -*-

{
    'name': 'Odoo13 Employee Contracts Types',
    'version': '13.0.1.0.0',
    'category': 'Generic Modules/Human Resources',
    'description': """
        Contract type in contracts
    """,
    'author': 'Cybrosys Techno Solutions, Odoo S.A.',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['hr','hr_contract'],
    'data': [
        'security/ir.model.access.csv',
        'views/contract_view.xml',
        'data/hr_contract_type_data.xml',
    ],
    'installable': True,
    'images': ['static/description/banner.png'],
    'auto_install': False,
    'application': False,
    'license': 'AGPL-3',
}