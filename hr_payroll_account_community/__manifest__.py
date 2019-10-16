# -*- coding: utf-8 -*-

{
    'name': 'Odoo13 Payroll Accounting',
    'category': 'Generic Modules/Human Resources',
    'description': """
Generic Payroll system Integrated with Accounting.
==================================================

    * Expense Encoding
    * Payment Encoding
    * Company Contribution Management
    """,
    'version': '13.0.1.0.0',
    'author': 'Cybrosys Techno Solutions, Odoo S.A.',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['hr_payroll_community', 'account'],
    'data': ['views/hr_payroll_account_views.xml'],
    'test': ['../account/test/account_minimal_test.xml'],
    'license': 'AGPL-3',
}
