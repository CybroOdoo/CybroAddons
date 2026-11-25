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
    'name': 'Accounting Dashboard',
    'version': '20.0.1.0.0',
    'category': 'Accounting',
    'summary': 'Interactive financial dashboard with key metrics, payment tracking, and visual analytics.',
    'description': """Odoo 20 Accounting Dashboard provides comprehensive financial insights,
allowing users to monitor key metrics such as open and paid invoices, total income,
unreconciled items, bank and cash balances, aged receivables and payables, and top customers
and vendors through interactive visualizations.""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['account'],
    'data': [
        'views/account_move_data.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'odoo_accounting_dashboard/static/src/scss/accounting_dashboard.scss',
            'odoo_accounting_dashboard/static/src/xml/accounting_dashboard.xml',
            'odoo_accounting_dashboard/static/src/js/accounting_dashboard.js',
        ],
        'web.assets_unit_tests': [
            'odoo_accounting_dashboard/static/tests/accounting_dashboard.test.js',
        ],
    },
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': True,
}
