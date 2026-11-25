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
    'name': "Thermal Invoice Report",
    'version': '20.0.1.0.0',
    'category': 'Accounting',
    'summary': 'A Module For Printing Thermal Invoice',
    'description': 'The Thermal Invoice Printing app enhances the '
                   'invoicing workflow in Odoo by enabling seamless '
                   'printing of compact, receipt-style invoices',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['account'],
    'data': [
        'data/account_move_data.xml',
        'report/account_move_reports.xml',
        'report/account_move_templates.xml',
    ],
    'assets': {
        'web.report_assets_common': [
            'thermal_invoice_report/static/src/css/thermal_style.css',
        ],
    },
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
