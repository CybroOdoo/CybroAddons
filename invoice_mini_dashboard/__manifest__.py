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
    'name': 'Invoice Mini Dashboard',
    'version': '20.0.1.0.0',
    'category': 'Accounting',
    'summary': 'Mini dashboard for invoicing module',
    'description': "Mini dashboard for the invoicing app with useful details"
                   " such as paid, unpaid and expected amounts and the count"
                   " of invoices by state.",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['account'],
    'data': [
        'views/account_move_views.xml'
    ],
    'assets': {
        'web.assets_backend': [
            'invoice_mini_dashboard/static/src/views/invoice_dashboard.js',
            'invoice_mini_dashboard/static/src/views/invoice_dashboard_templates.xml',
            'invoice_mini_dashboard/static/src/views/invoice_listview.js',
            'invoice_mini_dashboard/static/src/views/invoice_listview_templates.xml',
            'invoice_mini_dashboard/static/src/views/invoice_bill_dashboard.js',
            'invoice_mini_dashboard/static/src/views/invoice_bill_dashboard_templates.xml',
            'invoice_mini_dashboard/static/src/views/invoice_bill_listview.js',
            'invoice_mini_dashboard/static/src/views/invoice_bill_listview_templates.xml',
        ],
    },
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
