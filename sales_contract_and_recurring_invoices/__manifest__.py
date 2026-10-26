# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
{
    'name': 'Sales Contract and Recurring Invoices',
    'version': '20.0.1.0.0',
    'category': 'Sales/Accounting',
    'summary': """Create and manage sales contracts with automated recurring invoicing.""",
    'description': """This module helps to create sale contracts with recurring 
    invoices and enables access to all sale contracts from website portal.""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['sale_management', 'portal', 'website'],
    'data': [
        'security/ir.access.csv',
        'data/portal_entry_data.xml',
        'data/ir_cron_data.xml',
        'report/subscription_contract_reports.xml',
        'views/subscription_contracts_views.xml',
        'views/account_move_views.xml',
        'views/subscription_contracts_templates.xml',
        'report/subscription_contract_templates.xml',
    ],
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
