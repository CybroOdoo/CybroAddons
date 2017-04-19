# -*- coding: utf-8 -*-
{
    'name': "Employee Contracts Report",
    'summary': """Contract Report""",
    'description': """This Module Gives PDF Report on Contract Form.""",
    'category': 'Human Resources',
    'version': '0.1',
    'author': "Cybrosys Techno Solutions",
    'company': "Cybrosys Techno Solutions",
    'website': "http://www.cybrosys.com",
    'depends': ['base', 'hr', 'hr_contract', 'hr_payroll', 'report'],
    'data': [
        'views/contract_report.xml',
        'views/report_contract.xml',
    ],
    'images': ['static/description/banner.jpg'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
}
